# Agent roster

Specialised agents used on this build. Each has one job, one deliverable, and a
hard acceptance gate. The manager can order rework at any gate.

| File | Role | One job | Gate |
|---|---|---|---|
| `00-manager.md` | Boss / manager | Veto, rework, final acceptance | Nothing unverified ships |
| `01-landscape-researcher.md` | R1 | Prior-art and novelty research | Names real competitors with URLs and exact functional gaps |
| `02-adversarial-griller.md` | R2 | Attack the product idea | Every question has a recommended answer; explicit threat model |
| `03-architect.md` | A | Modules, seams, domain language | Shared vocabulary; no shallow modules |
| `04-implementer.md` | I | Write the code | `unittest` green, stdlib only, no invented features |
| `05-security-auditor.md` | S / T | Adversarial tests and 10-round audit | Probes must be able to fail; all rounds green |
| `06-release-engineer.md` | RE / AR | Architecture report, CI, license, zip | Golden unchanged, release checklist green |

## Rules that apply to every agent

1. Work strictly on the assigned part. No scope expansion, no "while I was here"
   refactors.
2. No fabrication. If a repo, URL, number, or capability could not be verified,
   write "unverified". A plausible-sounding guess is a defect.
3. No self-certification. "Done" means the gate command ran and printed PASS.
4. Rework is normal. The rework log in `docs/WORKFLOW.md` records eight real
   rejections; none were waived.
5. The manager's veto is final. An agent that disagrees still revises.

## What actually ran

R1 and R2 were delegated research subagents and produced the three reports in
`docs/research/`. A, I, S, T, AR and RE were executed in the main session under
the manager role, with their contracts recorded in these files. This distinction
is deliberate: it is not claimed that eight independent processes were spawned.
