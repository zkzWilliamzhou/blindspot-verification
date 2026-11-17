# Brainstorming / grilling — method reference (RECONSTRUCTED)

Sources:
- `github.com/obra/superpowers/tree/main/skills/brainstorming`
- `github.com/mattpocock/skills` — `grilling`, plus the short `grill-me` shim
- `github.com/Black-coffe/grill` — universal interrogation skill

None could be cloned. Notes come from public mirrors.

## The core `grill-me` instruction (also stored verbatim in `../mattpocock/grill-me/SKILL.md`)

```
---
name: grill-me
description: A relentless interview to sharpen a plan or design.
disable-model-invocation: true
---

Call the Skill tool with "grilling".
```

The expanded `grilling` procedure, as mirrored:

> Interview me relentlessly about every aspect of this plan until we reach a
> shared understanding. Walk down each branch of the design tree, resolving
> dependencies between decisions one-by-one. You MUST provide your recommended
> answer for every single question — never ask a question without also giving
> your own recommendation. This is mandatory, not optional. Ask the questions
> one at a time. If a question can be answered by exploring the codebase,
> explore the codebase instead.

## Superpowers brainstorming

Three modes — **Spike** (feasibility), **Bounded** (scoped change in an existing
codebase), **Architectural** (new project or large refactor) — decide how much
ceremony follows. A spec-document reviewer subagent checks completeness,
consistency, clarity, scope and YAGNI. Design is shown in small readable chunks.

## Black-coffe/grill (7 lenses)

`product` (principal engineer), `fund` (investment committee), `decision`
(decision scientist), `devil` (smartest opponent), `writing` (ruthless editor),
`ideas` (validation researcher — interrogates **and** researches prior art),
`proof` (fact-checker). Tracks an **assumption ledger** of verified ✓ vs
unverified ✗ assumptions, a decision log, a risk register, and a residual
ambiguity score. Optional Act 2: a fresh adversarial reviewer tries to refute
the finished brief.

## Applied here

The manager ran a self-grilling loop over the product idea: is the problem
real, does CI already solve it, what if the agent ignores it, is prose parsing
credible, is a local hash chain proof, what existing tools subsume it, why
would anyone star it, what must be cut, what is the biggest technical risk.
Every question carried a recommended answer. The `ideas` lens (interrogate
**and** research prior art) is what caught the first novelty report's false
"empty field" conclusion. The `devil` lens produced
`docs/research/03-adversarial-grill.md`, whose verdict was **BUILD BUT
NARROWLY** and which cut ten v1 features.

The assumption ledger survives as `docs/DESIGN.md`'s "Scope boundary, stated
plainly" table and `docs/THREAT_MODEL.md`'s list of unsupported claims.

## Status

NOT installed. Method applied from mirrored documentation only.
