# Workflow, agent roles, and the rework log

## The boss's rule

No agent output enters the codebase until it passes a gate. A gate failure
means the agent does that part again. Nothing is waved through because the
text sounded confident.

## Pipeline

```
  [M]  Manager (strict acceptance, veto, rework orders)
   |
   +-- [R1] Landscape & novelty researcher  --------> docs/research/*.md
   |         gate: must name concrete near-neighbours with URLs
   |         REWORK #1 issued: first report claimed an empty field; rejected
   |
   +-- [R2] Adversarial product griller -----------> docs/research/03-*.md
   |         gate: every question carries a recommended answer
   |         verdict: BUILD BUT NARROWLY; cut 10 features
   |
   +-- [M]  Synthesis: narrow to observation-channel integrity --------> DESIGN.md
   |
   +-- [A]  Architect: modules, seams, data model ------> CONTEXT.md, model.py
   +-- [I]  Implementer: one module per contract -------> blindspot/*.py
   +-- [T]  Test engineer: adversarial suite -----------> tests/test_*.py
   +-- [S]  Security auditor: 10-round harness --------> tests/audit_harness.py
   |         gate: every round must pass; probes must be real, not placeholders
   |         REWORK #2..#4 issued on real defects (see audit/round-*.md)
   |
   +-- [F]  Behavior-freeze gate ----------------------> tests/golden_check.py
   |         frozen BEFORE architecture work, checked AFTER
   |
   +-- [AR] Architecture reviewer ---------------------> docs/ARCHITECTURE.md
   |         gate: golden check must stay green; zero function change allowed
   |
   +-- [RE] Release engineer --------------------------> CI, license, skill, zip
             gate: round 10 release checklist all green
```

## Agent contracts

| ID | Role | Deliverable | Acceptance criteria | Outcome |
|---|---|---|---|---|
| M | Manager | Veto and rework orders | No unverified claim ships | 2 research reworks, 4 defect reworks |
| R1 | Landscape researcher | Novelty report | Names real competing projects with URLs and exact functional gaps | **REJECTED once**, reworked into v2 |
| R2 | Adversarial griller | Grill report | 10 questions, each with a recommended answer, explicit threat model | Accepted, drove 10 scope cuts |
| A | Architect | `CONTEXT.md`, data model | Shared vocabulary, no shallow modules | Accepted |
| I | Implementer | 13 Python modules | `unittest` green, no third-party imports | Accepted after defect fixes |
| T | Test engineer | 46 tests | Adversarial cases, not happy-path only | Accepted |
| S | Security auditor | 10-round harness | Real probes that can and did fail | Round 1 found 14 real defects |
| F | Freeze gate | `baseline.json` | 14 scenarios normalized, byte-comparable | Green before and after refactor |
| AR | Architecture reviewer | Architecture report | Uses the design vocabulary; deletion test applied; golden unchanged | Accepted |
| RE | Release engineer | CI, license, skill, zip | All release files present and valid | Accepted |

Full role prompts live in `agents/`.

## Rework log (actual, not decorative)

| # | Agent | Why rejected | What changed |
|---|---|---|---|
| 1 | R1 | "No verified tool owns the claim-to-evidence contract" missed at least seven concrete projects, including `agent-receipts` and PALA-1. | Full re-research: `novelty-landscape-v2.md` accounts for `nocap`, `alibi`, `Reverify`, `CodeVetter`, `anti-fake-complete`, `honestly`, Palimpsests and `authenticiq/agent-receipts`. Verdict downgraded to "crowded field, narrow slice remains". |
| 2 | I | Secrets in the command string itself leaked into the stored report. | Whole-envelope recursive redaction; digests still cover unredacted bytes. |
| 3 | I | `&>`, `\|&`, `<(`, shell control keywords and `tail -f` were silently accepted. | Tokenizer-level refusal of unsupported constructs; non-terminating filters removed from the supported set. |
| 4 | I | `--deny-net` broke assignment-prefix commands; `RLIMIT_FSIZE` tied to `--max-output` was destroying ground truth before hashing. | Fixed wrapper with `shlex.quote`, fixed generous independent FSIZE limit, full-stream digests restored. |
| 5 | I | `--max-bytes` cap produced more bytes than the cap. | Bounded head/tail window with an explicit marker. |
| 6 | I | Terminal escape sequences from captured output reached the user's terminal. | `sanitize_terminal` on text and hook output. |
| 7 | S / harness | Golden baseline was frozen against a non-executable fixture, and audit probes were too weak to fail. | Fixtures invoke `python3` explicitly; probes rewritten to actually surface control bytes and false greens. |
| 8 | AR | SHA-256 logic duplicated in `capture.py`; `blindspot.__main__` could not be imported. | Centralized hashing in `hashing.py`; guarded `__main__`; introduced deep `pipeline.py` module. |

## Gates, in order, every time

1. `python3 -m unittest discover -s tests -p 'test_*.py' -v` — 46 tests.
2. `python3 tests/golden_check.py --check` — 14 frozen scenarios, zero diff.
3. `python3 tests/audit_harness.py` — 10 rounds, all probes pass.
4. `python3 -m blindspot demo` — expected exit 1 with `MISLEADING`.
5. Release file checklist — round 10.

A gate failure blocks the next stage. The architecture pass ran only after the
freeze was green, and was accepted only after `--check` remained green.
