# 01 — Landscape & novelty researcher (R1)

## Mission

Establish whether the proposed primary function already exists. Attack your own
"empty field" conclusion before reporting it.

## Inputs

Candidate product idea: a local claim-to-evidence ledger for AI coding agents.

## Deliverable

Markdown report with concrete project names, URLs, stated function, and a
precise functional-gap table.

## Acceptance gate — FAILED ON FIRST PASS

The first report claimed no verified product owned the claim-to-evidence
contract. It was **rejected** because it missed at least seven near-neighbours.
Rework order:

> Account for `nocap`, `BOTIROFF-D/alibi`, `Reverify`, `CodeVetter`,
> `ardianwn/anti-fake-complete`, `honestly`, Palimpsests / PALA-1, and
> `authenticiq/agent-receipts`. Evaluate two narrow unoccupied slices, name the
> closest incumbent for each, search specifically for exit-code laundering and
> output-truncation detection, and state explicitly that absolute global novelty
> cannot be proven.

## Reworked acceptance criteria (met)

- `novelty-landscape-v2.md` states plainly that the field is crowded and only
  narrow slices remain.
- Candidate A (observation-channel integrity) is ranked less occupied than
  Candidate B (staleness graph), with `honestly` named as the closest incumbent
  and the exact difference stated.
- Searches for `|| true`, `set +e`, ANSI-hidden failures, output truncation and
  "agent saw only the last line" reported as a public-search null result, not as
  proof of absence.
- Every unverifiable claim marked unverified.

## Outputs

`docs/research/01-novelty-landscape-v1.md` (rejected, kept as evidence),
`docs/research/02-novelty-landscape-v2-rework.md` (accepted).
