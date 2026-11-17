# 05 — Security auditor & test engineer (S / T)

## Mission

Write tests that can fail, and audit the program from more than eight directions.
A probe that cannot fail is a fake probe.

## Deliverables

- `tests/test_blindspot.py` — 46 adversarial unit tests.
- `tests/golden_check.py` — behavior freeze across 14 scenarios.
- `tests/audit_harness.py` — 10-round audit with real probes, writing
  `audit/round-N.md`.
- `audit/round-*.md` — evidence of what each round actually caught.

## The ten rounds

| # | Focus | Probes |
|---|---|---|
| 1 | Functional correctness and CLI contract | 5 |
| 2 | Secret and privacy handling | 6 |
| 3 | Shell parser safety and injection surface | 12 |
| 4 | Replay fidelity and resource behaviour | 7 |
| 5 | Execution safety and sandbox-lite guarantees | 6 |
| 6 | Ledger integrity, tamper detection, concurrency | 6 |
| 7 | Terminal and output safety | 5 |
| 8 | Full regression, behavior freeze, documentation accuracy | 6 |
| 9 | Architecture invariants | 5 |
| 10 | Final release gate | 6 |

Total: 64 probes per full run. The user asked for **over 8 rounds**; 10 were
run, twice (before and after the architecture pass), against the live package.

## First-pass results (preserved, not hidden)

```
Round 1: 4/5    Round 2: 4/6    Round 3: 6/12   Round 4: 6/7   Round 5: 4/6
Round 6: 6/6    Round 7: 5/5    Round 8: 3/6    Round 9/10: added later
OVERALL: FAIL
```

Fourteen real defects were found and fixed. Round 9 later found two architecture
defects (duplicate SHA-256 logic, unimportable `__main__`), also fixed.

## Rework ordered by the manager

The first golden baseline was frozen against a non-executable fixture (exit 126)
and several round-7 probes could not fail. Ordered: real `python3` fixtures and
probes that actually surface control bytes and false greens. Reworked and
re-frozen before the architecture pass.

## Final gate

All 10 rounds PASS, 46 unit tests PASS, `golden_check.py --check` reports
"behavior unchanged across 14 frozen scenarios".
