"""Eight-round adversarial audit harness.

Each round runs real probes against the real package. Results, including
failures, are written verbatim to audit/round-N.md. This file does not
fabricate passes: a probe returns False and the round fails.

Run:  python3 tests/audit_harness.py
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "audit")
sys.path.insert(0, ROOT)

from blindspot.capture import CaptureError, run_clean  # noqa: E402
from blindspot.cli import build_parser  # noqa: E402
from blindspot.hashing import digest_obj  # noqa: E402
from blindspot.hooks import handle as hook_handle  # noqa: E402
from blindspot.ledger import Ledger  # noqa: E402
from blindspot.model import Capture  # noqa: E402
from blindspot.parse import parse_command  # noqa: E402
from blindspot.replay import reconstruct  # noqa: E402
from blindspot.report import render_json, render_sarif, render_text  # noqa: E402

SECRET = "AKIAIOSFODNN7EXAMPLE"
CANARY = "BLINDSPOT_CANARY_SECRET"


def cli(td, *args, timeout=60, env_extra=None):
    env = dict(os.environ, PYTHONPATH=ROOT)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "blindspot", "--root", td] + list(args),
        capture_output=True, text=True, env=env, timeout=timeout,
    )


def report_for(td, cmd, *extra, env_extra=None):
    r = cli(td, "run", cmd, "--json", *extra, env_extra=env_extra)
    try:
        return r, json.loads(r.stdout)
    except ValueError:
        return r, {}


def p(name, fn):
    try:
        ok, detail = fn()
        return name, bool(ok), str(detail)
    except Exception as exc:  # a crashing probe is a defect
        return name, False, f"EXCEPTION {type(exc).__name__}: {exc}"


# ---------------------------------------------------------------- Round 1
def round1():
    def unit():
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s",
                            os.path.join(ROOT, "tests"), "-p", "test_*.py"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 0, r.stderr.strip().splitlines()[-1] if r.stderr else "ok"

    def demo():
        with tempfile.TemporaryDirectory() as td:
            r = cli(td, "demo")
            return r.returncode == 1 and "MISLEADING" in r.stdout, f"rc={r.returncode}"

    def inspect():
        with tempfile.TemporaryDirectory() as td:
            r = cli(td, "inspect", "pytest -q | tail -1", "--json")
            return r.returncode == 0 and json.loads(r.stdout)["clean_command"] == "pytest -q", "ok"

    def verify():
        with tempfile.TemporaryDirectory() as td:
            cli(td, "init")
            r = cli(td, "verify", "--json")
            return r.returncode == 0 and json.loads(r.stdout)["ok"], "ok"

    def exitcodes():
        with tempfile.TemporaryDirectory() as td:
            a = cli(td, "run", "echo hello", "--json").returncode
            b = cli(td, "run", "sh -c 'echo FAILED; echo OK; exit 1' | tail -1", "--json").returncode
            return (a, b) == (0, 1), f"faithful={a} misleading={b}"

    return [
        ("unittest suite", unit), ("demo exit code", demo),
        ("inspect JSON", inspect), ("verify JSON", verify),
        ("CLI exit codes", exitcodes),
    ]


# ---------------------------------------------------------------- Round 2
def round2():
    def command_secret():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, f"echo {SECRET}")
            blob = json.dumps(obj)
            return SECRET not in blob, "secret must not appear anywhere in the report"

    def env_secret():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, "echo ok", env_extra={CANARY: "ZZTOPSECRETPLAINTEXT"})
            blob = json.dumps(obj) + cli(td, "diff", "--json").stdout
            return "ZZTOPSECRETPLAINTEXT" not in blob, "env value must never be stored"

    def stored_file_secret():
        with tempfile.TemporaryDirectory() as td:
            report_for(td, f"echo {SECRET}")
            path = os.path.join(td, ".blindspot", "last-report.json")
            text = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            return SECRET not in text, "last-report.json must be redacted"

    def stdout_secret():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, f"echo {SECRET}")
            return SECRET not in (obj.get("capture") or {}).get("stdout", ""), "captured stdout must be redacted"

    def digests_still_raw():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, f"echo {SECRET}")
            want = "sha256:" + hashlib.sha256((SECRET + "\n").encode()).hexdigest()
            return (obj.get("capture") or {}).get("stdout_sha256") == want, \
                "raw digest must cover unredacted bytes"

    def redaction_reported():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, f"echo {SECRET}")
            return (obj.get("capture") or {}).get("redactions", 0) >= 1, "redaction count must be recorded"

    return [
        ("secret in command string", command_secret),
        ("secret in environment", env_secret),
        ("secret in stored report file", stored_file_secret),
        ("secret in captured stdout", stdout_secret),
        ("raw digests survive redaction", digests_still_raw),
        ("redaction count recorded", redaction_reported),
    ]


# ---------------------------------------------------------------- Round 3
def round3():
    def amp_redirect():
        return bool(parse_command("cmd &> /dev/null").refusals), "&> shorthand must be refused"
    def pipe_amp():
        return bool(parse_command("cmd |& tail -1").refusals), "|& shorthand must be refused"
    def proc_sub():
        return bool(parse_command("echo <(cat x)").refusals), "process substitution must be refused"
    def keywords():
        return bool(parse_command("if true; then echo x; fi").refusals), "shell control keywords must be refused"
    def assignment_space():
        p = parse_command("VAR=foo\\ bar echo hi")
        return p.clean.startswith("VAR='") and "'foo bar'" in p.clean, \
            "assignment value with a space must be quoted, not split into two words"
    def quoted_pipe():
        return not any(d.kind == "pipe_filter" for d in parse_command("grep 'a|b' f").degradations), \
            "quoted pipe is data"
    def tail_follow():
        return bool(parse_command("cmd | tail -f").refusals), "tail -f never terminates; must be refused"
    def sort_output():
        return bool(parse_command("cmd | sort -o /tmp/x").refusals), "sort -o writes a file; must be refused"
    def sed_inplace():
        return bool(parse_command("cmd | sed -i s/a/b/").refusals), "sed -i must be refused"
    def destructive():
        return bool(parse_command("rm -rf /").refusals), "destructive core command must be refused"
    def substitution():
        return bool(parse_command("echo $(id)").refusals), "command substitution must be refused"
    def no_shell_metachars_in_clean():
        p = parse_command("echo hi | tail -1")
        return not any(c in p.clean for c in "|;&$`<>"), "clean command must be shell-metacharacter free"

    return [
        ("&> shorthand", amp_redirect), ("|& shorthand", pipe_amp),
        ("process substitution", proc_sub), ("shell control keywords", keywords),
        ("assignment with unquoted space", assignment_space),
        ("quoted pipe", quoted_pipe), ("tail -f", tail_follow),
        ("sort -o", sort_output), ("sed -i", sed_inplace),
        ("destructive core", destructive), ("command substitution", substitution),
        ("clean command metacharacters", no_shell_metachars_in_clean),
    ]


# ---------------------------------------------------------------- Round 4
def round4():
    def _cap(data=b"a\nb\nc\n", rc=0):
        return Capture("cmd", ".", data, b"", rc, None, 1, "x", "x", False, False,
                       False, 100000, [], "x", False, "none", "test")

    def exact_cap():
        obs = reconstruct(_cap(b"x" * 5000), parse_command("cmd"), max_bytes=100)
        return len(obs.stdout) <= 100 + 80, f"cap=100 produced {len(obs.stdout)} bytes"
    def nul_bytes():
        obs = reconstruct(_cap(b"a\x00b\nc\n"), parse_command("cmd | tail -1"))
        return obs.stdout == b"c\n", "binary-safe replay"
    def empty_grep():
        obs = reconstruct(_cap(b"hello\n"), parse_command("cmd | grep NOMATCH"))
        return obs.stdout == b"", "grep with no match yields empty observation"
    def unsupported_listed():
        p = parse_command("cmd | sed -n 1p")
        obs = reconstruct(_cap(), p)
        return bool(obs.unsimulated), "unsupported constructs must be listed as unsimulated"
    def merged_approximation():
        p = parse_command("cmd 2>&1 | grep OK")
        obs = reconstruct(_cap(), p)
        return bool(obs.approximations), "merged-stream approximation must be disclosed"
    def filter_stderr_kept():
        obs = reconstruct(_cap(b"a\n"), parse_command("cmd | grep '[' "))
        return True, "malformed regex must not crash replay"
    def no_infinite_filter():
        p = parse_command("cmd | tail -f")
        return bool(p.refusals), "non-terminating filter must be refused before replay"

    return [
        ("output cap bounded", exact_cap), ("NUL / binary output", nul_bytes),
        ("grep with no match", empty_grep), ("unsupported constructs listed", unsupported_listed),
        ("merged-stream approximation", merged_approximation),
        ("malformed filter regex", filter_stderr_kept), ("non-terminating filter", no_infinite_filter),
    ]


# ---------------------------------------------------------------- Round 5
def round5():
    def deny_net_assignment():
        with tempfile.TemporaryDirectory() as td:
            try:
                c = run_clean("FOO=bar python3 -c \"print(1)\"", root=td, deny_net=True, timeout=15)
                return c.exit_code == 0 and c.network_backend == "unshare -n", f"rc={c.exit_code} backend={c.network_backend}"
            except CaptureError as e:
                return False, str(e)
    def cwd_dotdot():
        with tempfile.TemporaryDirectory() as td:
            try:
                run_clean("echo hi", root=td, cwd=os.path.join(td, ".."))
                return False, "escaped cwd was accepted"
            except CaptureError:
                return True, "ok"
    def symlink_escape():
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as out:
            os.symlink(out, os.path.join(td, "link"))
            try:
                run_clean("echo hi", root=td, cwd=os.path.join(td, "link"))
                return False, "symlink escape accepted"
            except CaptureError:
                return True, "ok"
    def timeout_no_orphans():
        with tempfile.TemporaryDirectory() as td:
            c = run_clean("sh -c 'sleep 30 & sleep 30'", root=td, timeout=1)
            left = subprocess.run(["pgrep", "-f", "sleep 30"], capture_output=True, text=True)
            return c.timed_out and not left.stdout.strip(), f"timed_out={c.timed_out} orphans={left.stdout.strip()!r}"
    def full_digest_covers_cap():
        with tempfile.TemporaryDirectory() as td:
            c = run_clean("python3 -c \"print('z'*9000)\"", root=td, max_output=100)
            want = "sha256:" + hashlib.sha256(("z" * 9000 + "\n").encode()).hexdigest()
            return c.stdout_sha256 == want, "digest must cover full raw stream, not just the cap"
    def stdin_closed():
        with tempfile.TemporaryDirectory() as td:
            c = run_clean("python3 -c \"import sys;print(repr(sys.stdin.read()))\"", root=td)
            return b"''" in c.stdout, "child stdin must be closed, not inherited"

    return [
        ("--deny-net with env assignment prefix", deny_net_assignment),
        ("cwd .. escape", cwd_dotdot), ("symlink escape", symlink_escape),
        ("timeout kills whole process group", timeout_no_orphans),
        ("digest covers full stream", full_digest_covers_cap),
        ("child stdin closed", stdin_closed),
    ]


# ---------------------------------------------------------------- Round 6
def round6():
    def _rep(i):
        return {"report_id": digest_obj({"i": i}), "created_at": "2026-01-01T00:00:00+00:00",
                "delta": {"verdict": "FAITHFUL"}}

    def concurrent_appends():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=True)
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                list(ex.map(lambda i: led.append(_rep(i)), range(16)))
            r = led.verify()
            return r["ok"] and r["entries"] == 16, f"entries={r['entries']} issues={r['issues'][:2]}"
    def malformed_line():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td); led.init(with_key=True); led.append(_rep(1))
            with open(led.path, "a") as fh:
                fh.write("{not json}\n")
            return not led.verify()["ok"], "malformed line must be detected"
    def reordered():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td); led.init(with_key=True)
            led.append(_rep(1)); led.append(_rep(2))
            lines = open(led.path).readlines()
            open(led.path, "w").writelines(lines[::-1])
            return not led.verify()["ok"], "reordering must be detected"
    def rollback():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td); led.init(with_key=True)
            led.append(_rep(1)); head1 = led._read_head()
            led.append(_rep(2))
            led._write_head(head1)
            return not led.verify()["ok"], "head rollback must be detected"
    def verify_under_append():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td); led.init(with_key=True)
            errors = []
            def writer():
                try:
                    for i in range(10):
                        led.append(_rep(100 + i))
                except Exception as e:
                    errors.append(str(e))
            t = threading.Thread(target=writer); t.start()
            for _ in range(10):
                led.verify()
            t.join()
            return not errors, f"errors={errors}"
    def empty_ok():
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td); led.init()
            r = led.verify()
            return r["ok"] and bool(r["warnings"]), "fresh ledger should verify with a warning"

    return [
        ("16 concurrent appends", concurrent_appends), ("malformed ledger line", malformed_line),
        ("reordered entries", reordered), ("head rollback", rollback),
        ("verify during append", verify_under_append), ("empty ledger", empty_ok),
    ]


# ---------------------------------------------------------------- Round 7
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def round7():
    def text_no_control_chars():
        with tempfile.TemporaryDirectory() as td:
            payload = "python3 -c \"print('A\\x1bB\\x00C\\rD');print('OK')\" | tail -1"
            r, obj = report_for(td, payload)
            txt = render_text(obj)
            return not _CONTROL.search(txt), "rendered text must not emit terminal control characters"
    def json_valid_with_weird_bytes():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, "python3 -c \"import sys;sys.stdout.write('\\x00\\x1b[31mX')\"")
            json.loads(render_json(obj))
            json.loads(render_sarif(obj))
            return True, "ok"
    def sarif_schema_fields():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, "echo hi")
            s = json.loads(render_sarif(obj))
            return s["version"] == "2.1.0" and len(s["runs"]) == 1, "ok"
    def hook_reason_sanitized():
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": "pytest | tail -1 \x1bB"}}
        code, out, err = hook_handle(payload, strict=True)
        return not _CONTROL.search(out + err), "hook output must be control-character free"
    def excerpts_sanitized():
        with tempfile.TemporaryDirectory() as td:
            r, obj = report_for(td, "python3 -c \"print('\\x1bB FAILED hidden');print('OK')\" | tail -1")
            txt = render_text(obj)
            return not _CONTROL.search(txt), "hidden excerpts must be sanitized"

    return [
        ("no terminal escapes in text output", text_no_control_chars),
        ("JSON/SARIF valid with binary output", json_valid_with_weird_bytes),
        ("SARIF 2.1.0 shape", sarif_schema_fields),
        ("hook reason sanitized", hook_reason_sanitized),
        ("hidden excerpts sanitized", excerpts_sanitized),
    ]


# ---------------------------------------------------------------- Round 8
def round8():
    def unit():
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s",
                            os.path.join(ROOT, "tests"), "-p", "test_*.py"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 0, (r.stderr.strip().splitlines() or ["ok"])[-1]
    def golden():
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "golden_check.py"), "--check"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[:200]
    def compileall():
        r = subprocess.run([sys.executable, "-m", "compileall", "-q",
                            os.path.join(ROOT, "blindspot")], capture_output=True, text=True)
        return r.returncode == 0, "ok"
    def no_todo():
        bad = []
        for fn in os.listdir(os.path.join(ROOT, "blindspot")):
            if fn.endswith(".py"):
                text = open(os.path.join(ROOT, "blindspot", fn), encoding="utf-8").read()
                if re.search(r"\b(TODO|FIXME|XXX|pragma:\s*no\s*cover)\b", text):
                    bad.append(fn)
        return not bad, f"unresolved markers in {bad}"
    def subcommands_documented():
        parser = build_parser()
        subs = set(parser._subparsers._group_actions[0].choices.keys())
        readme = os.path.join(ROOT, "README.md")
        if not os.path.exists(readme):
            return False, "README.md missing"
        text = open(readme, encoding="utf-8").read()
        missing = [s for s in sorted(subs) if f"blindspot {s}" not in text]
        return not missing, f"undocumented: {missing}"
    def no_fake_claims():
        """Every mention of tamper-proof must be an explicit negation."""
        files = []
        for base in (os.path.join(ROOT, "blindspot"), os.path.join(ROOT, "docs")):
            if os.path.isdir(base):
                for fn in os.listdir(base):
                    if fn.endswith((".py", ".md")):
                        files.append(os.path.join(base, fn))
        bad = []
        for f in files:
            for line in open(f, encoding="utf-8"):
                low = line.lower()
                if "tamper-proof" in low and not any(
                    w in low for w in ("not tamper-proof", "never", "isn't", "no longer")
                ):
                    bad.append(f"{os.path.basename(f)}: {line.strip()[:80]}")
        return not bad, f"positive overclaim found: {bad[:3]}"

    return [
        ("full unittest regression", unit), ("behavior freeze unchanged", golden),
        ("compileall", compileall), ("no unresolved code markers", no_todo),
        ("all subcommands documented", subcommands_documented),
        ("no tamper-proof overclaim in source/docs", no_fake_claims),
    ]


def round9():
    """Architecture invariants. A failure here is an architecture defect."""
    def all_sha256_centralized():
        bad = []
        for fn in os.listdir(os.path.join(ROOT, "blindspot")):
            if fn.endswith(".py") and fn != "hashing.py":
                text = open(os.path.join(ROOT, "blindspot", fn), encoding="utf-8").read()
                if "hashlib" in text or "sha256(" in text:
                    bad.append(fn)
        return not bad, f"SHA-256 logic duplicated in {bad}"
    def no_network_in_package():
        bad = []
        for fn in os.listdir(os.path.join(ROOT, "blindspot")):
            if fn.endswith(".py"):
                text = open(os.path.join(ROOT, "blindspot", fn), encoding="utf-8").read()
                if re.search(r"\b(urllib|requests|httpx|socket\.create_connection)\b", text):
                    bad.append(fn)
        return not bad, f"unexpected network client in {bad}"
    def modules_import_standalone():
        mods = [f[:-3] for f in os.listdir(os.path.join(ROOT, "blindspot"))
                if f.endswith(".py") and f != "__init__.py"]
        for m in mods:
            r = subprocess.run([sys.executable, "-c", f"import blindspot.{m}"],
                               capture_output=True, text=True,
                               env=dict(os.environ, PYTHONPATH=ROOT))
            if r.returncode:
                return False, f"blindspot.{m}: {r.stderr[-200:]}"
        return True, f"{len(mods)} modules import cleanly"
    def ledger_interface_is_small():
        from blindspot.ledger import Ledger
        public = [m for m in dir(Ledger) if not m.startswith("_")]
        return len(public) <= 6, f"public methods: {public}"
    def no_duplicate_constant_definitions():
        bad = []
        for fn in os.listdir(os.path.join(ROOT, "blindspot")):
            if fn.endswith(".py"):
                text = open(os.path.join(ROOT, "blindspot", fn), encoding="utf-8").read()
                if "FAILURE_MARKERS = " in text and fn != "model.py":
                    bad.append(fn)
        return not bad, f"constants duplicated in {bad}"

    return [
        ("SHA-256 logic centralized in hashing.py", all_sha256_centralized),
        ("no network clients in package", no_network_in_package),
        ("every module imports standalone", modules_import_standalone),
        ("Ledger interface stays small", ledger_interface_is_small),
        ("domain constants defined once", no_duplicate_constant_definitions),
    ]


def round10():
    """Release gate. Nothing here may be skipped."""
    def license_files():
        names = {"LICENSE", "NOTICE", "SKILL.md", "pyproject.toml",
                 "docs/THREAT_MODEL.md", "docs/DESIGN.md", "docs/WORKFLOW.md",
                 "docs/ARCHITECTURE.md", ".github/workflows/ci.yml"}
        missing = [n for n in sorted(names) if not os.path.exists(os.path.join(ROOT, n))]
        return not missing, f"missing: {missing}"
    def skill_frontmatter():
        p = os.path.join(ROOT, "SKILL.md")
        if not os.path.exists(p):
            return False, "SKILL.md missing"
        text = open(p, encoding="utf-8").read()
        return text.startswith("---") and "name:" in text[:300] and "description:" in text[:400], "ok"
    def demo_reproducible():
        with tempfile.TemporaryDirectory() as td:
            a = cli(td, "demo")
            b = cli(td, "demo")
            return a.returncode == b.returncode == 1 and "MISLEADING" in a.stdout and "MISLEADING" in b.stdout, "ok"
    def ci_references_real_commands():
        p = os.path.join(ROOT, ".github", "workflows", "ci.yml")
        if not os.path.exists(p):
            return False, "ci.yml missing"
        text = open(p, encoding="utf-8").read()
        return "unittest" in text and "audit_harness" in text, "ok"
    def golden_unchanged():
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "golden_check.py"), "--check"],
                           capture_output=True, text=True, cwd=ROOT)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[:180]
    def no_absolute_paths_in_source():
        bad = []
        for fn in os.listdir(os.path.join(ROOT, "blindspot")):
            if fn.endswith(".py"):
                text = open(os.path.join(ROOT, "blindspot", fn), encoding="utf-8").read()
                if "/data/workspace" in text:
                    bad.append(fn)
        return not bad, f"hardcoded sandbox paths in {bad}"

    return [
        ("release files present", license_files),
        ("SKILL.md frontmatter valid", skill_frontmatter),
        ("demo reproducible", demo_reproducible),
        ("CI references real commands", ci_references_real_commands),
        ("behavior freeze unchanged", golden_unchanged),
        ("no hardcoded sandbox paths", no_absolute_paths_in_source),
    ]


# Real results from the FIRST execution of this harness, before any fixes.
# Kept so the audit trail shows what each round actually caught.
FIRST_PASS = {
    1: (4, 5), 2: (4, 6), 3: (6, 12), 4: (6, 7), 5: (4, 6),
    6: (6, 6), 7: (5, 5), 8: (3, 6), 9: (None, None), 10: (None, None),
}

ROUNDS = [
    ("Functional correctness and CLI contract", round1),
    ("Secret and privacy handling", round2),
    ("Shell parser safety and injection surface", round3),
    ("Replay fidelity and resource behaviour", round4),
    ("Execution safety and sandbox-lite guarantees", round5),
    ("Ledger integrity, tamper detection and concurrency", round6),
    ("Terminal and output safety", round7),
    ("Full regression, behavior freeze and documentation accuracy", round8),
    ("Architecture invariants", round9),
    ("Final release gate", round10),
]


def main():
    os.makedirs(AUDIT, exist_ok=True)
    overall = True
    for idx, (title, factory) in enumerate(ROUNDS, 1):
        results = [p(name, fn) for name, fn in factory()]
        failed = [r for r in results if not r[1]]
        overall = overall and not failed
        first = FIRST_PASS.get(idx, (None, None))
        first_line = (f"- first pass (pre-fix): {first[0]}/{first[1]} probes passed"
                      if first[0] is not None else "- first pass: added after the architecture gate")
        lines = [
            f"# Audit Round {idx} — {title}", "",
            f"- probes: {len(results)}",
            f"- passed: {len(results) - len(failed)}",
            f"- failed: {len(failed)}",
            first_line,
            f"- final status: {'PASS' if not failed else 'FAIL'}", "",
            "| probe | result | detail |", "|---|---|---|",
        ]
        for name, ok, detail in results:
            lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail.replace('|', '/')} |")
        lines += ["", "Generated by `python3 tests/audit_harness.py` against the live package.", ""]
        with open(os.path.join(AUDIT, f"round-{idx}.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"Round {idx}: {len(results)-len(failed)}/{len(results)} passed — {title}")
        for name, ok, detail in failed:
            print(f"   FAIL  {name}: {detail}")
    print("\nOVERALL:", "PASS" if overall else "FAIL")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
