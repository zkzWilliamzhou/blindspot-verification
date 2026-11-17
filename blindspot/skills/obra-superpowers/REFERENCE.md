# obra/superpowers — workflow reference (RECONSTRUCTED)

Source: `github.com/obra/superpowers` (MIT, Jesse Vincent / Prime Radiant).
Repository could not be cloned or fetched directly; the workflow below comes
from public setup guides and mirrors. Star counts in those mirrors are
unverified and are not repeated as fact here.

## The chain of skills

1. **brainstorming** — refine a rough idea through questions, explore
   alternatives, evaluate trade-offs, present the design in readable sections
   for validation, save a design document. Classifies work as Spike, Bounded,
   or Architectural.
2. **using-git-worktrees** — after sign-off, create an isolated workspace on a
   new branch and confirm a clean test baseline.
3. **writing-plans** — break work into 2–5 minute tasks with exact file paths,
   complete code, and verification steps. Granularity test: a junior engineer
   with no project context can follow it.
4. **subagent-driven-development** — dispatch a fresh subagent per task, with
   two-stage review (spec compliance, then code quality). Alternative:
   `executing-plans` in one session.
5. **test-driven-development** — RED → GREEN → REFACTOR per task. Code written
   before a failing test is deleted.
6. **requesting-code-review** — review between tasks; critical issues block
   progress.
7. **finishing-a-development-branch** — verify tests, offer merge / PR / keep /
   discard, clean up the worktree.

Values: YAGNI, DRY, true TDD, spec-first, no guessing. A spec reviewer
subagent checks completeness, consistency, clarity, scope, and YAGNI.

## Applied here

- Brainstorm → design → plan → implement → review → finish. See
  `docs/WORKFLOW.md`.
- Fresh subagent per specialised role via delegated research agents.
- Two-stage review: spec compliance (did the agent answer the brief?) then
  quality (is it true?). The R1 novelty report failed stage 1 and was sent back.
- RED-style adversarial probes: `tests/audit_harness.py` was written to be able
  to fail, and it did — 14 defects on the first pass.
- Plans were bite-sized and file-specific.

## Deviations

No git worktrees were used (single sandbox workspace), and no interactive
sign-off was requested because the user asked for autonomous execution until
done. Those two gates were replaced by the frozen behavior baseline and the
manager veto.

## Status

NOT installed. Method applied from mirrored documentation only.
