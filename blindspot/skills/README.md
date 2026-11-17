# External skills: provenance and installation status

**Read this before believing any of these are installed.**

## Hard fact

This sandbox cannot reach GitHub. Measured during the session:

| Target | Result |
|---|---|
| `https://github.com/...` (git clone) | HTTP 403 |
| `https://raw.githubusercontent.com/...` | timeout / 301 then blocked |
| `https://registry.npmjs.org/skills` | HTTP 403 |
| `npx skills add ...` | impossible, registry unreachable |

Therefore **none of the GitHub skill repositories below were cloned, installed,
or executed**. `git clone --depth 1 https://github.com/hardikpandya/stop-slop.git`
was attempted and failed with 403. `web_fetch` succeeded for a small number of
raw files and public mirror pages; those results are recorded below.

Anything marked **RECONSTRUCTED** is a summary written from publicly mirrored
documentation. It is not byte-identical to upstream, is not executable, and
must not be presented as an installed skill. Anything marked **VERBATIM** is a
short upstream text retrieved through a public mirror, reproduced with its
source noted.

## What the user asked for, and its real status

| Requested | Upstream source | Status here | Used in this project? |
|---|---|---|---|
| Anthropic skills | `github.com/anthropics/skills` | RECONSTRUCTED reference | Yes — the Agent Skills format (frontmatter `name` + `description`, one folder per skill) shaped the shipped root `SKILL.md` |
| Matt Pocock skills | `github.com/mattpocock/skills` | One VERBATIM file + RECONSTRUCTED reference | Yes — `grill-me` drove self-grilling; `improve-codebase-architecture` drove `docs/ARCHITECTURE.md` |
| Vercel Labs agent skills | `github.com/vercel-labs/agent-skills`, `vercel-labs/skills` | RECONSTRUCTED skill list | Indirectly — structured CLI/report conventions |
| stop-slop | `github.com/hardikpandya/stop-slop` (also a separate `tomerose/stop-slop`) | RECONSTRUCTED rules | Yes — prose in README and docs was edited against its anti-slop checks |
| Brainstorming skills | `obra/superpowers` `skills/brainstorming`, `Black-coffe/grill` | RECONSTRUCTED method | Yes — structured exploration, one-question-at-a-time interrogation, assumption ledger |
| Superpowers skills | `github.com/obra/superpowers` | RECONSTRUCTED workflow | Yes — brainstorm → plan → TDD → review → finish; subagent-driven development and two-stage review |
| improve-codebase-architecture | `mattpocock/skills/skills/engineering/...` | RECONSTRUCTED method | Yes — applied in the architecture pass, see `docs/ARCHITECTURE.md` |

## What IS actually installed and shipped

One skill: the repository root `SKILL.md`, authored in this project, in the
Agent Skills format, MPL-2.0. It is the skill we believe useful **for this
program** — it teaches an agent to check its observation channel before
claiming success. It has no network, no dependencies, and no external runtime.

## Files in this directory

- `anthropics-skills/REFERENCE.md` — spec summary, source noted.
- `mattpocock/grill-me/SKILL.md` — VERBATIM short upstream text from a public mirror.
- `mattpocock/improve-codebase-architecture/REFERENCE.md` — method notes.
- `vercel-labs/REFERENCE.md` — skill catalogue.
- `stop-slop/REFERENCE.md` — rules used for prose editing.
- `obra-superpowers/REFERENCE.md` — workflow chain.
- `brainstorming/REFERENCE.md` — brainstorming and interrogation method.

## How to actually install them on a networked machine

```
npx skills add anthropics/skills --skill '*' -y
npx skills add mattpocock/skills --skill "improve-codebase-architecture" -y
npx skills add mattpocock/skills --skill "grilling" -y
npx skills add vercel-labs/agent-skills -y
npx skills add hardikpandya/stop-slop -y
npx skills add obra/superpowers --skill brainstorming -y
/plugin marketplace add anthropics/skills
```

Then copy the root `SKILL.md` into your agent's skills directory, or run
`blindspot hook --strict` as a Claude Code `PreToolUse` hook.

**Do not claim these were installed in this session.** They were not.
