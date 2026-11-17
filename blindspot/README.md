# blindspot

**Your agent only saw the last line.**

`blindspot` measures what a shell command hid from an AI coding agent. It runs
the command once, captures the real stdout, stderr and exit status, then
reconstructs the filtered view the agent would have read. It reports the exact
difference between the two.

```
$ blindspot run "pytest -q | tail -1"

  VERDICT       : MISLEADING
  real exit     : 1
  agent saw exit: 0
  stdout        : 812 bytes real / 12 bytes seen

  hidden stdout:
    FAILED tests/test_auth.py::test_expired_token
    FAILED tests/test_auth.py::test_missing_scope
    2 failed, 6 passed in 0.41s
```

The agent saw `6 passed` and exit status 0. The real run failed twice.

## What this is

A coding agent reads the output of the shell commands it writes. Those commands
often destroy the evidence they run on:

| Command | What the agent sees | What happened |
|---|---|---|
| `pytest \| tail -1` | one summary line | full failure list dropped, exit status replaced by `tail`'s 0 |
| `npm test \|\| true` | full output, exit 0 | real non-zero exit discarded |
| `make 2>/dev/null` | no errors | every compiler error discarded |
| `pytest \| grep passed` | `6 passed` | `2 failed` filtered out |
| `pytest \| head -20` | first 20 lines | summary at the bottom never arrives |

`blindspot` does not verify correctness, intent, or test quality. It answers one
question: **how much of the real execution reached the agent's context?**

## What this is not

- Not a test runner. It runs the command you give it once.
- Not a CI replacement. CI remains the durable merge gate.
- Not a sandbox or a security boundary. `--deny-net` on Linux is the only
  enforced isolation.
- Not an AI detector or a lie detector. It never reads an agent's prose.
- Not a proof system. The local hash chain is tamper-evident, not tamper-proof.

## Install

Python 3.10 or newer. No runtime dependencies, no daemon, no account, no network.

```sh
git clone <this-repo>
cd blindspot
python3 -m blindspot demo
```

Or copy the `blindspot/` package anywhere on `PYTHONPATH`. For a wrapper script,
see `pyproject.toml`.

## Commands

| Command | What it does |
|---|---|
| `blindspot init` | Create `.blindspot/` ledger. `--key` adds an HMAC key with mode 0600. |
| `blindspot inspect "<cmd>"` | Static analysis only. Never executes anything. |
| `blindspot run "<cmd>"` | Execute once, capture ground truth, report the delta. |
| `blindspot diff` | Show the most recent report. |
| `blindspot verify` | Check ledger integrity. Detects edited, deleted and reordered entries. |
| `blindspot demo` | Self-contained synthetic 30-second demonstration. |
| `blindspot hook` | Claude Code hook adapter. Reads hook JSON on stdin. |

`blindspot run` options:

```
--timeout N          kill the command after N seconds (default 30)
--max-output N       cap stored ground truth at N bytes (default 1000000)
--max-bytes N        simulate a harness output cap of N bytes (0 disables)
--deny-net           require Linux `unshare -n`; refuse to run otherwise
--strict             exit 1 on any degradation, not just MISLEADING
--allow-destructive  permit core commands such as rm (still refused by default)
--cwd PATH           run inside a subdirectory of the project root
--json               canonical JSON envelope
--sarif              SARIF 2.1.0 for CI annotations
```

Exit codes: `0` faithful or degraded, `1` misleading (or `--strict` with any
degradation), `2` refusal or usage error.

## How it works

1. `parse.py` reads the command and lists every observation-degrading construct.
   It derives a clean command by removing those constructs. Anything it cannot
   reconstruct safely becomes a refusal, and nothing is executed.
2. `capture.py` runs the clean command **once**. It captures raw stdout, stderr,
   exit status, duration and digests. The child gets a minimal environment,
   closed stdin, POSIX resource limits, its own process group, and optional
   network isolation.
3. `replay.py` runs the recorded filters (`tail`, `grep`, `head`, `wc`, ...)
   as real binaries over those captured bytes. It also replays redirections,
   exit-code laundering, stream merging and output caps. Unsupported constructs
   are reported as unsimulated, never guessed.
4. `delta.py` compares the two views and emits `FAITHFUL`, `DEGRADED` or
   `MISLEADING` with the exact hidden lines and hidden failure markers.
5. `ledger.py` appends a content-addressed, hash-chained entry. `blindspot verify`
   recomputes every link.

Ground truth comes from one execution. The agent's view is reconstructed from
captured bytes, so no side-effecting command runs twice.

## Hook integration

`blindspot hook` supports the Claude Code hook JSON shape only. It performs
static inspection inside the hook and never executes the command there.

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 -m blindspot hook --strict"
      }]
    }]
  }
}
```

With `--strict`, a critical degradation exits 2 and Claude Code feeds the
explanation back to the agent. Without it, the hook allows the call and attaches
a warning. A `PostToolUse` hook cannot undo an executed command, so this adapter
stays passive there. Other agent harnesses are not claimed.

`SKILL.md` in this repo follows the Agent Skills format so a compatible agent
can load the same guidance directly.

## The canonical envelope

`blindspot run --json` emits a versioned object with `report_id`,
`degradations`, `capture`, `observation`, `delta` and `limitations`. Digests
cover the unredacted bytes; stored text is scrubbed for common credential
shapes. Other tools can consume this envelope without trusting this CLI.

## Limits you should read

See `docs/THREAT_MODEL.md`. The short version:

- A local adversary with write access can replace the ledger directory, head,
  or key. The chain detects edits, not wholesale replacement.
- The replay uses a defined subset of filters. Unsupported ones are refused.
- stdout and stderr interleaving under `2>&1` is approximated.
- Wall-clock timestamps are local and unanchored.
- A passing command still proves nothing about whether it was the right command.

## Development

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/golden_check.py --freeze   # before any refactor
python3 tests/audit_harness.py           # ten adversarial rounds (64 probes)
python3 tests/golden_check.py --check    # after any refactor
```

`tests/golden_check.py` freezes behaviour across 14 scenarios. The architecture
pass in `docs/ARCHITECTURE.md` was gated on that check staying green.

## License

MPL-2.0. See `LICENSE` and `NOTICE`.
