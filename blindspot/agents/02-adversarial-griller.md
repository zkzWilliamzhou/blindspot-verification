# 02 — Adversarial product griller (R2)

## Mission

Attack the idea. Never validate it. One round at a time; every question carries
your own recommended answer.

## Deliverable

Markdown grill report with ten questions, a threat model, scope cuts, and a
verdict of BUILD / DON'T BUILD / BUILD BUT NARROWLY.

## Questions (all answered, none evaded)

1. Is the problem real, and who loses time or money?
2. Why adopt this when CI already gates merges?
3. What if the agent simply does not use it?
4. Is regex claim parsing credible, or will it get the project mocked?
5. Is a local hash chain proof? Name exact failure modes.
6. What existing tools most nearly subsume this? What if a vendor ships it?
7. Why would anyone star it? What is the 30-second demo? Why die at 300 stars?
8. What must be cut from v1?
9. Naming, licensing, positioning, biggest technical risk.
10. Final verdict with the exact narrowed scope.

## Verdict (accepted)

**BUILD BUT NARROWLY.** Renamed to `evident` in the report; the manager later
chose `blindspot` to describe the actual mechanism. The report cut:

- natural-language claim parsing,
- LLM judging,
- universal hook injection,
- full environment capture,
- unrestricted filesystem diffing,
- interactive command support,
- remote storage,
- "tamper-proof" claims,
- confidence percentages,
- correctness/compliance promises.

It also corrected a statistic: 22.58% referred to visible, user-corrected
failure episodes, not 22.58% of all agent tasks. That correction is preserved in
the report and is not repeated as a marketing number anywhere in the product.

## Acceptance gate (met)

Explicit threat model with rollback and key-theft worked examples; six-command
v1 scope; `SUPPORTED`/`CONTRADICTED`/`UNVERIFIED`-style three-state verdicts;
no fabricated growth projections.

## Output

`docs/research/03-adversarial-grill.md`
