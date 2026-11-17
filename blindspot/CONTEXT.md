# Domain glossary

Shared vocabulary used by `docs/ARCHITECTURE.md` and the architecture report.
Terms are used exactly here; we do not drift into "component", "service",
"API", or "boundary".

- **module** — one Python file with a single reason to change.
- **interface** — the public functions a module exposes. The interface is the
  test surface: tests and the frozen baseline exercise the interface, not the
  internals.
- **depth** — ratio of behaviour hidden behind an interface to the size of that
  interface. A deep module lets a caller do a lot while learning little.
- **seam** — a place where two modules meet and could be swapped. One adapter
  makes a hypothetical seam; two adapters make a real one.
- **adapter** — a thin translation layer at a seam. `replay.py` is the adapter
  between captured bytes and real filter binaries.
- **leverage** — how much behaviour one module's interface unlocks.
  `pipeline.measure_command` has high leverage: one call drives five modules.
- **locality** — related behaviour lives close together. Hashing all lives in
  `hashing.py`; execution safety all lives in `capture.py`.
- **deletion test** — would deleting a suspected shallow module concentrate
  complexity, or merely move it? "Concentrates" is the signal to keep it.

## Domain facts

- **ground truth**: the bytes and exit status captured from exactly one real
  execution of the clean command.
- **observation**: what the agent would have seen, reconstructed by replaying
  recorded degradations over ground truth.
- **degradation**: a construct that removes or alters evidence (pipe filter,
  redirection, exit-code laundering, stream merge, output cap).
- **verdict**: `FAITHFUL`, `DEGRADED`, or `MISLEADING`. No numeric trust score.
- **receipt / ledger entry**: a content-addressed, hash-chained record. It is
  tamper-evident, not tamper-proof.
- **refusal**: a condition under which the command is NOT executed. Refusals
  produce a static report, never synthetic evidence.

## ADRs (decisions not to re-litigate)

- ADR-001: one real execution only. Never re-run side-effecting commands to
  obtain a second observation.
- ADR-002: no natural-language claim parsing. Free-form prose is outside scope.
- ADR-003: tamper-evident local chain, no external anchor in v1.
- ADR-004: zero runtime dependencies; standard library only.
- ADR-005: three verdicts only. No confidence percentages.
