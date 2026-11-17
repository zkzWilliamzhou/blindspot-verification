# Verification record

Recorded on 2026-11-12, Asia/Shanghai. These are real command outputs from the
final run against the live package after all reworks.

## 1. Unit tests

```
$ python3 -m unittest discover -s tests -p 'test_*.py' -v
Ran 46 tests in 4.881s
OK
```

## 2. Behavior freeze (function preservation)

```
$ python3 tests/golden_check.py --check
behavior unchanged across 14 frozen scenarios
```

The baseline in `tests/golden/baseline.json` was frozen **before** the
architecture pass and checked **after** it. It compares 14 scenarios across
verdicts, exit codes, degradations, hidden lines, excerpts, digests,
approximations and refusals. Zero differences. No function of the program
changed during the architecture work.

## 3. Ten-round adversarial audit

```
$ python3 tests/audit_harness.py
Round 1: 5/5 passed — Functional correctness and CLI contract
Round 2: 6/6 passed — Secret and privacy handling
Round 3: 12/12 passed — Shell parser safety and injection surface
Round 4: 7/7 passed — Replay fidelity and resource behaviour
Round 5: 6/6 passed — Execution safety and sandbox-lite guarantees
Round 6: 6/6 passed — Ledger integrity, tamper detection and concurrency
Round 7: 5/5 passed — Terminal and output safety
Round 8: 6/6 passed — Full regression, behavior freeze and documentation accuracy
Round 9: 5/5 passed — Architecture invariants
Round 10: 6/6 passed — Final release gate

OVERALL: PASS
```

64 probes per full run. Per-round evidence, including the first-pass failures,
is in `audit/round-1.md` … `audit/round-10.md`.

The first execution of this harness failed 14 probes across rounds 1–5, 7 and 8.
Those were real defects (secret leakage, unsafe shell constructs, a broken
`--deny-net` wrapper, ground truth destroyed by a resource limit, an unbounded
output cap, terminal escape injection), not decorative failures. All were fixed
and re-audited. Round 9 later found two architecture defects, also fixed.

## 4. Demo smoke test

```
$ python3 -m blindspot demo
DEMO_RC=1 (expected 1)
  VERDICT       : MISLEADING
  real exit     : 1
  agent saw exit: 0
```

`blindspot demo` deliberately exits 1: the false-green demo is the point.

## 5. Release file checklist

All present: `LICENSE`, `NOTICE`, `SKILL.md`, `pyproject.toml`, `Makefile`,
`CONTEXT.md`, `README.md`, `.github/workflows/ci.yml`, `docs/DESIGN.md`,
`docs/WORKFLOW.md`, `docs/THREAT_MODEL.md`, `docs/ARCHITECTURE.md`,
`examples/demo.sh`, `tests/golden/baseline.json`, `docs/research/*.md`,
`skills/README.md`, `agents/README.md`, `audit/round-*.md`.

## 6. What was NOT verified

- The external GitHub skills were not installed. `git clone` and the npm
  registry both returned 403. See `skills/README.md`.
- The MPL-2.0 text is reproduced from the official public license text; the
  upstream `mozilla.org` URL returned 403 in this sandbox.
- Absolute global novelty is not proven. `docs/DESIGN.md` and
  `docs/research/02-novelty-landscape-v2-rework.md` state the field is crowded
  and only a narrow slice remains open.
- No star count, adoption figure, or growth projection is claimed anywhere.
- Cross-platform behaviour on macOS and Windows was not executed here; the
  audit ran on Linux. Non-POSIX limitations are documented in the threat model.
