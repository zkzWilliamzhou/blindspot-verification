"""Static analysis of a shell command's observation channel.

We deliberately support a narrow, well-defined subset. Anything we cannot
faithfully reconstruct is reported as a refusal instead of being guessed.
That is the core honesty contract of this tool.
"""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import List, Tuple

from .model import CleanCommand, Degradation

# Filters whose behaviour we can reproduce by running the real binary on
# captured bytes. Anything else is reported but never silently simulated.
SUPPORTED_FILTERS = {
    "head": {"-n", "-c", "--lines", "--bytes", "-q", "-v", "--help", "--version"},
    "tail": {"-n", "-c", "--lines", "--bytes", "-q", "-v", "--help", "--version"},
    "grep": {"-i", "-E", "-F", "-P", "-v", "-c", "-n", "-m", "-e", "-o", "-q",
             "-l", "-L", "-w", "-x", "-A", "-B", "-C", "--color", "--", "-h", "-H"},
    "egrep": {"-i", "-v", "-c", "-n", "-m", "-e", "-o", "-q", "-l", "-L", "-w", "-x"},
    "fgrep": {"-i", "-v", "-c", "-n", "-m", "-e", "-o", "-q", "-l", "-L", "-w", "-x"},
    "wc": {"-l", "-w", "-c", "-m", "-L", "--lines", "--words", "--bytes", "--chars"},
    "cut": {"-d", "-f", "-b", "-c", "-s", "--delimiter", "--fields", "--bytes",
            "--characters", "--complement", "--only-delimited", "-z"},
    "tr": {"-d", "-s", "-c", "-t"},
    "sort": {"-r", "-n", "-u", "-k", "-t", "-f", "-b", "-h", "-V", "-o"},
    "uniq": {"-c", "-d", "-u", "-i", "-f", "-s", "-w"},
}

# Filters that can write files, invoke interpreters, or otherwise have
# semantics we refuse to reconstruct.
UNSAFE_FILTERS = {
    "sed", "awk", "perl", "python", "python3", "node", "ruby", "php", "jq",
    "xargs", "tee", "less", "more", "echo", "printf", "cat", "sh", "bash",
    "env", "export", "eval", "exec", "read", "while", "for", "if", "curl", "wget",
}

LAUNDER_TAILS = {"true", ":", "exit", "echo", "printf", "noop"}

SHELL_KEYWORDS = {
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done",
    "case", "esac", "function", "select", "coproc", "{", "}",
}

_ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_GLOB = re.compile(r"[*?\[\]{}~]")
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@dataclass
class Tok:
    text: str
    kind: str  # word | op
    quoted: bool = False


_OPS = ("2>&1", "1>&2", ">&2", "2>>", "1>>", ">>", "2>", "1>", ">", "||", "&&", "|", ";", "&", "<<")


def tokenize(cmd: str) -> Tuple[List[Tok], List[str]]:
    """Small, conservative shell tokenizer. Returns (tokens, unsupported_reasons)."""
    out: List[Tok] = []
    unsupported: List[str] = []
    i, n = 0, len(cmd)
    while i < n:
        c = cmd[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "#":
            break  # comment to end of line
        if c == "`":
            unsupported.append("backtick command substitution")
            break
        if cmd.startswith("$(", i):
            unsupported.append("$() command substitution")
            break
        if cmd.startswith("<<", i):
            unsupported.append("here-document")
            break
        for bad in ("&>", "|&", "<(", ">(", "&>>"):
            if cmd.startswith(bad, i):
                unsupported.append(f"unsupported shell construct {bad!r}")
                break
        else:
            bad = None
        if bad:
            break
        matched = None
        for op in _OPS:
            if cmd.startswith(op, i):
                matched = op
                break
        if matched:
            out.append(Tok(matched, "op"))
            i += len(matched)
            continue
        if c in "'\"":
            quote = c
            j = i + 1
            buf = []
            while j < n:
                if quote == '"' and cmd[j] == "\\" and j + 1 < n:
                    buf.append(cmd[j + 1])
                    j += 2
                    continue
                if cmd[j] == quote:
                    break
                buf.append(cmd[j])
                j += 1
            if j >= n:
                unsupported.append("unterminated quote")
                break
            out.append(Tok("".join(buf), "word", quoted=True))
            i = j + 1
            continue
        # plain word
        j = i
        buf = []
        while j < n and cmd[j] not in " \t\r\n":
            if cmd[j] == "\\" and j + 1 < n:
                buf.append(cmd[j + 1])
                j += 2
                continue
            if cmd[j] in "'\"":
                q = cmd[j]
                j += 1
                while j < n and cmd[j] != q:
                    buf.append(cmd[j])
                    j += 1
                if j < n:
                    j += 1
                continue
            nxt = None
            for op in _OPS:
                if cmd.startswith(op, j):
                    nxt = op
                    break
            if nxt:
                break
            if cmd[j] == "#" and j > i:
                break
            buf.append(cmd[j])
            j += 1
        if buf:
            word = "".join(buf)
            if "$( " in word or "$(" in word or "`" in word:
                unsupported.append("command substitution inside word")
            out.append(Tok(word, "word"))
        if j == i:
            i += 1
        else:
            i = j
    return out, unsupported


def _split_top(tokens: List[Tok], sep: str) -> List[List[Tok]]:
    parts: List[List[Tok]] = [[]]
    for t in tokens:
        if t.kind == "op" and t.text == sep:
            parts.append([])
        else:
            parts[-1].append(t)
    return [p for p in parts if p]


def _words(seg: List[Tok]) -> List[str]:
    return [t.text for t in seg if t.kind == "word"]


_NUMERIC_SHORT = re.compile(r"^-[0-9]+[A-Za-z]?$|^-[ncm][0-9]+$")


def _validate_filter(argv: List[str]) -> Tuple[bool, str]:
    if not argv:
        return False, "empty filter segment"
    name = argv[0]
    if name in UNSAFE_FILTERS:
        return False, f"filter {name!r} has side effects or non-reproducible semantics"
    if name not in SUPPORTED_FILTERS:
        return False, f"filter {name!r} is not in the supported replay set"
    safe = SUPPORTED_FILTERS[name]
    for arg in argv[1:]:
        if arg.startswith("-"):
            flag = arg.split("=", 1)[0]
            if flag in safe or flag.startswith("--color") or _NUMERIC_SHORT.match(arg):
                continue
            return False, f"filter {name!r} uses unsupported flag {arg!r}"
        # Replay passes argv directly, never a shell, so glob-looking regex
        # patterns such as grep 'a.*' are data and need no special handling.
    if any(a in ("-i", "--in-place") for a in argv):
        return False, "in-place editing filter"
    if "-o" in argv and name == "sort":
        return False, "sort -o writes to a file"
    return True, ""


# Replay applies the recorded argv verbatim; no shell expansion happens there.
def parse_command(cmd: str, allow_destructive: bool = False) -> CleanCommand:
    """Produce degradations, a derived clean command, and replay argv segments."""
    tokens, unsupported = tokenize(cmd)
    degradations: List[Degradation] = []
    refusals: List[str] = list(unsupported)
    filter_segments: List[List[str]] = []

    if not tokens:
        return CleanCommand(cmd, "", [], [], ["empty command"])

    # Split into clauses on ; && || so we can detect laundering suffixes.
    clauses: List[Tuple[str, List[Tok]]] = []
    current: List[Tok] = []
    current_op = ""
    for t in tokens:
        if t.kind == "op" and t.text in (";", "&&", "||"):
            clauses.append((current_op, current))
            current, current_op = [], t.text
        else:
            current.append(t)
    clauses.append((current_op, current))

    # Detect exit-code laundering in trailing clauses.
    for op, clause in clauses[1:]:
        ws = _words(clause)
        if not ws:
            continue
        if op == "||" and (ws[0] in LAUNDER_TAILS or (ws[0] == "exit" and len(ws) > 1 and ws[1] == "0")):
            degradations.append(Degradation(
                "exit_laundered",
                f"the {op!r} branch replaces the real exit status with success",
                f"{op} {' '.join(ws)}", "critical", True, ws))
        elif op == ";" and (ws[0] in ("true", ":") or (ws[0] == "exit" and len(ws) > 1 and ws[1] == "0")):
            degradations.append(Degradation(
                "exit_laundered",
                "a trailing '; true' discards the real exit status",
                f"; {' '.join(ws)}", "critical", True, ws))

    if any(_words(c[1])[:2] == ["set", "+e"] for c in clauses):
        degradations.append(Degradation(
            "exit_laundered", "'set +e' disables exit-on-error", "set +e", "critical", True, []))
    pipefail_requested = any(
        _words(c[1])[:3] == ["set", "-o", "pipefail"] for c in clauses
    )

    # "set +e" / "set -o pipefail" are preambles, not the command under test.
    main_clause: List[Tok] = []
    for _, clause in clauses:
        ws = _words(clause)
        if ws[:1] == ["set"] and (ws[1:2] in (["+e"], ["-o"], ["-e"])):
            continue
        main_clause = clause
        break
    if not main_clause:
        main_clause = clauses[0][1] if clauses else []

    segments = _split_top(main_clause, "|")
    if len(segments) > 1 and not pipefail_requested:
        degradations.append(Degradation(
            "pipefail_absent",
            "without 'set -o pipefail' the shell reports the LAST pipeline stage's exit status, "
            "so an upstream failure is silently replaced by the filter's success",
            "|", "critical", True, []))

    # Redirections in the core segment.
    core_words: List[str] = []
    skip_next = False
    for idx, t in enumerate(segments[0]):
        if skip_next:
            skip_next = False
            continue
        if t.kind == "op" and t.text in (">", "1>", ">>", "1>>", "2>", "2>>", "2>&1", "1>&2", ">&2"):
            target = ""
            if idx + 1 < len(segments[0]) and segments[0][idx + 1].kind == "word":
                target = segments[0][idx + 1].text
                skip_next = True
            if t.text in ("2>&1", "1>&2", ">&2"):
                degradations.append(Degradation(
                    "stream_merged", "stdout and stderr are merged; ordering is approximated in replay",
                    t.text, "warning", True, []))
            elif target == "/dev/null":
                stream = "stderr" if t.text.startswith("2") else "stdout"
                degradations.append(Degradation(
                    f"{stream}_suppressed", f"{stream} is redirected to /dev/null",
                    f"{t.text}{target}", "critical", True, []))
            else:
                degradations.append(Degradation(
                    "unsupported", f"redirection to {target!r} is not reconstructed",
                    f"{t.text}{target}", "warning", False, []))
                refusals.append(f"redirection to {target!r}")
            continue
        if t.kind == "word":
            core_words.append(t.text)

    # Filters (all segments after the first).
    for seg in segments[1:]:
        argv = _words(seg)
        ok, why = _validate_filter(argv)
        if not ok:
            degradations.append(Degradation(
                "unsupported", why, " ".join(argv), "warning", False, argv))
            refusals.append(why)
            continue
        degradations.append(Degradation(
            "pipe_filter",
            f"output passes through {argv[0]!r}; the agent sees only what survives",
            " ".join(argv), "critical" if argv[0] in ("head", "tail", "grep", "egrep", "fgrep", "wc") else "warning",
            True, argv))
        filter_segments.append(argv)

    # ANSI control sequences in the command string itself.
    if _ANSI.search(cmd):
        degradations.append(Degradation(
            "ansi", "command contains ANSI escape sequences", "\\x1b", "info", True, []))

    # Safety checks on the derived clean command.
    for t in segments[0]:
        if t.kind == "word" and not t.quoted and t.text in SHELL_KEYWORDS:
            refusals.append(f"shell control keyword {t.text!r} cannot be safely reconstructed")
    for w in core_words:
        if _GLOB.search(w) and not w.startswith("-"):
            refusals.append(f"glob metacharacter in {w!r} cannot be safely reconstructed")
        if not allow_destructive and w in (
            "sudo", "su", "rm", "mv", "chmod", "chown", "dd", "mkfs", "shutdown", "reboot"
        ):
            refusals.append(f"destructive command {w!r} is refused by default (use --allow-destructive)")

    clean = _rebuild(core_words)
    return CleanCommand(cmd, clean, filter_segments, degradations, _dedupe(refusals))


def _rebuild(words: List[str]) -> str:
    """Quote every word. Assignments keep their `NAME=` prefix unquoted."""
    parts = []
    for w in words:
        m = _ASSIGNMENT.match(w) if "\n" not in w else None
        if m:
            parts.append(m.group(1) + "=" + shlex.quote(m.group(2)))
        else:
            parts.append(shlex.quote(w))
    return " ".join(parts)


def _dedupe(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
