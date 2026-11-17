# 06 — Architecture reviewer & release engineer (AR / RE)

## Mission (AR)

Apply `improve-codebase-architecture` without changing one function of the
program. Use the vocabulary in `CONTEXT.md` exactly.

## Applied deepening opportunities

- **Strong, applied:** concentrate the measurement contract into the deep
  `pipeline.py` module. `cli.py` now adapts arguments; the pipeline owns
  ordering, redaction-before-digest, and envelope construction.
- **Strong, applied:** move `stream_digest_and_head` into `hashing.py` so one
  module owns every SHA-256 computation.
- **Worth exploring, applied:** make `__main__.py` an import-safe adapter.
- **Speculative, rejected:** splitting `ledger.py` into reader/writer — the
  deletion test says it would just move complexity across a seam.
- **Speculative, rejected:** a filter plugin registry — YAGNI, and it would
  widen the interface for an ecosystem that does not exist.

## The non-negotiable gate

```
freeze  ->  refactor  ->  golden_check.py --check
```

`tests/golden/baseline.json` was frozen **before** the architecture pass and is
checked **after**. It compares 14 scenarios across verdicts, exit codes,
degradations, hidden lines, excerpts, digests, approximations and refusals. A
single changed value fails the gate. Result: unchanged. No function changed.

## Mission (RE)

Ship a repository a stranger can verify in one command.

## Deliverables

- `LICENSE` (MPL-2.0), `NOTICE`, `pyproject.toml`, `Makefile`.
- `.github/workflows/ci.yml` — Python 3.10/3.11/3.12, unittest, golden check,
  audit harness, demo smoke test.
- Root `SKILL.md` in the Agent Skills format.
- `docs/DESIGN.md`, `docs/WORKFLOW.md`, `docs/THREAT_MODEL.md`,
  `docs/ARCHITECTURE.md`, `docs/research/*.md`.
- `skills/` provenance, `agents/` roster, `examples/demo.sh`.
- The final zip.

## Acceptance gate (round 10)

All release files exist; SKILL.md frontmatter valid; demo reproducible; CI
references real commands; behavior freeze unchanged; no hardcoded sandbox paths
in source.

## Honesty constraints

- External GitHub skills were **not** installed: clone and npm registry both
  returned 403. `skills/README.md` states this plainly.
- The MPL-2.0 text is reproduced from the official public license text; the
  upstream URL itself returned 403 in this sandbox.
- No star count is promised or predicted.
