# improve-codebase-architecture — method notes (RECONSTRUCTED)

Upstream: `github.com/mattpocock/skills/tree/main/skills/engineering/improve-codebase-architecture`.
Retrieved from a public mirror page (Vibehackers / TypingMind skill listing).
Could not be cloned or installed in this sandbox.

## Method applied in `docs/ARCHITECTURE.md`

**Purpose:** surface architectural friction and propose **deepening
opportunities** — refactors that turn shallow modules into deep ones. Aim is
testability and AI-navigability.

**Vocabulary, used exactly:** module, interface, depth, seam, adapter, leverage,
locality. The method explicitly forbids drifting into "component", "service",
"API", or "boundary".

**Principles:**
- The **deletion test**: would deleting a suspected shallow module concentrate
  complexity, or just move it? "Yes, concentrates" is the signal to keep it.
- **The interface is the test surface.**
- **One adapter = hypothetical seam, two = real.**
- Domain language in `CONTEXT.md` names good seams; ADRs record decisions not
  to re-litigate.

**Process:**
1. **Explore** — scope before scanning (YAGNI). Weight recently changed files
   (`git log --oneline` hot spots) unless the user named a direction. Read
   `CONTEXT.md` and ADRs first. Walk the codebase organically and note where
   understanding one concept requires bouncing between many small modules,
   where modules are shallow, where pure functions were extracted for
   testability while the real bugs hide in how they are called (no locality),
   and where tightly coupled modules leak across seams.
2. **Present candidates as an HTML report** — self-contained, with
   Tailwind/Mermaid, before/after visualisation, and a recommendation strength
   of `Strong`, `Worth exploring`, or `Speculative`.
3. **Grill the chosen candidate** with the `/grilling` skill, apply side effects
   inline, and keep the domain model current.

## Deviation in this project

The upstream method asks for a self-contained HTML report. This project ships a
Markdown report (`docs/ARCHITECTURE.md`) with Mermaid diagrams instead, because
the deliverable is a source repository, not a browser artifact. The vocabulary,
deletion test, scoping rule, and recommendation strengths were applied without
change.

## Hard gate added by the manager

No function of the program may change. `tests/golden_check.py` froze 14
scenarios before the architecture pass and was checked after it. The report
documents the before/after gate results. A refactor that changes a verdict, a
hidden line, a digest, or a refusal is rejected.

## Status

NOT installed. Method applied from mirrored documentation only.
