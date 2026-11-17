# 03 — Architect (A)

## Mission

Define the module structure, the domain language, and the data model, so the
implementer never has to guess a shape.

## Deliverables

- `CONTEXT.md`: glossary (module, interface, depth, seam, adapter, leverage,
  locality), domain facts, and five ADRs.
- `blindspot/model.py`: plain dataclasses only. No behaviour lives in the data
  model, keeping the on-disk envelope stable.

## Module map decided

| Module | One reason to change |
|---|---|
| `model.py` | The shape of a report changes |
| `hashing.py` | Canonical serialization or digest policy changes |
| `redact.py` | Secret patterns change |
| `parse.py` | The supported shell subset changes |
| `capture.py` | Execution safety or capture policy changes |
| `replay.py` | The replayable degradation set changes |
| `delta.py` | Verdict semantics change |
| `ledger.py` | Chain or head format changes |
| `report.py` | Rendering changes |
| `hooks.py` | Claude Code hook shape changes |
| `pipeline.py` | The measurement contract changes |
| `cli.py` | CLI arguments or exit codes change |

## ADRs (not re-litigated later)

- ADR-001 one real execution only.
- ADR-002 no natural-language claim parsing.
- ADR-003 tamper-evident chain, no external anchor in v1.
- ADR-004 zero runtime dependencies.
- ADR-005 three verdicts only, no confidence score.

## Acceptance gate (met)

Every module has a single reason to change. The envelope is versioned
(`schema_version`, `tool_version`, `report_id`). Digests cover unredacted bytes
while stored text is scrubbed. No module imports a third-party package.
