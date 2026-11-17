# Design: blindspot

## The one-sentence product

`blindspot` measures how much of a real shell execution reached an AI coding
agent's context, and reports the exact difference.

```
blindspot run "pytest -q | tail -1"
```

Ground truth: 812 bytes, exit 1, two failures. The agent's view: 12 bytes,
exit 0, `6 passed`. The delta is the product.

## Why this gap, and only this gap

The first research pass concluded that no tool owned "claim → evidence
verification" for coding agents. That conclusion was wrong, and the manager
rejected it. A second pass found a crowded field:

| Near-neighbor | Primary function | Precise difference from blindspot |
|---|---|---|
| `nocap` / `@zoeyx/nocap` (verified via public mirror) | Re-runs declared checks and lets the real exit code overrule an agent's self-report | Adjudicates a claim. Does not audit the observation channel that produced the claim, and does not report hidden lines. |
| `BOTIROFF-D/alibi` | Rolls code back to the pre-fix state and reruns new tests; a test that still passes tested nothing | Counterfactual test meaningfulness. blindspot does not judge test quality. |
| `honestly` (Claude Code hook) | Blocks evasive commands such as `pytest \| head` and challenges unsupported "tests pass" prose | Gate at command-shape level and prose level. blindspot executes once and produces a byte-exact delta with hidden lines and both exit codes. |
| `Reverify` | Deterministic verification of structured claims about PE/ELF/Mach-O binaries; local ledger of verified facts | Artifact-level binary facts. blindspot is about shell observation, not binary structure. |
| `CodeVetter` | Task-bound execution-backed verification of agent revisions; fail-closed JSON/Markdown/HTML evidence bundles | Runs the repository's own checks against a revision. blindspot measures what a single command hid. |
| `anti-fake-complete` | L0..L6 evidence ladder plus validator rejecting "verified" below required level | Structural evidence levels. blindspot does not parse prose or grade evidence levels. |
| `authenticiq/agent-receipts` | Neutral JSON action-receipt contract, Merkle inclusion batches, Rust verifier | Receipt format and verifier. blindspot does not define a general action-receipt contract. |
| Palimpsests / PALA-1 | Frozen hash-chained offline-verifiable portable audit-log format | Log format. blindspot's ledger is a local implementation detail, not a portable format. |
| `hardikpandya/stop-slop`, `unslop` | Prose/code-diff style linting | Unrelated to execution evidence. |
| Hollow Validation Checker (skill) | Static detection of `\|\| true` and empty assertions in skill definitions | Static lint of skill files. blindspot runs the command and measures the real result. |

The remaining narrow opening is **observation-channel integrity**: the exact
delta between what a command actually did and what the agent was able to see.
`honestly` is the closest incumbent; it blocks the bad shape rather than
measuring the fidelity loss. A direct search for tools whose primary function
is exit-code-laundering detection, output-truncation detection, or clean-channel
re-execution produced a public-search null result. That is not proof of global
novelty: private repos, unreachable pages, and future releases are outside the
evidence. See `docs/research/02-novelty-landscape-v2-rework.md`.

## What makes it plausibly useful

- Every agent harness truncates output. Every agent uses pipes to manage context.
  The failure mode is universal and independent of vendor.
- The 30-second demo shows a failure, not a green badge. It is falsifiable and
  reversible: change nothing, and `MISLEADING` repeats; add `set -o pipefail`,
  and the exit-status laundering disappears.
- The output is a versioned JSON envelope. A reviewer can paste it into a PR,
  a CI job can fail on it, and SARIF annotations point at the degradation.
- Zero runtime dependencies, no daemon, no account, no network, no model calls.

## What was deliberately cut from v1

1. Natural-language claim extraction from an agent's final summary.
2. LLM-based judging of claims.
3. Cross-agent universal hook injection. Only the Claude Code hook shape is
   handled, and it is documented as such.
4. Generic recursive filesystem diffing. No unbounded directory scanning.
5. Full environment capture. Only a scrubbed digest of non-allowlisted values.
6. Windows kernel sandboxing, interactive commands, pseudo-terminal capture.
7. Remote storage, transparency-log publication, external anchoring.
8. Any promise of correctness, non-repudiation, compliance, or "AI lie detection".
9. Confidence scores. Three verdicts only: `FAITHFUL`, `DEGRADED`, `MISLEADING`.
10. Automatic rewriting of the agent's command. The tool refuses unsupported
    constructs; it never guesses a reconstruction.

## Scope boundary, stated plainly

| blindspot can tell you | blindspot cannot tell you |
|---|---|
| The real exit status vs the reported one | Whether the command was the right test |
| Exactly which stdout/stderr lines were hidden | Whether hidden lines mattered |
| Whether failure markers were filtered out | Whether the test suite is sufficient |
| Which constructs degraded the observation | Whether the agent lied on purpose |
| Whether the ledger was edited or truncated | Whether the whole ledger directory was replaced |

## Honest note on the 105k-star ambition

No tool can be engineered into a star count, and no star count is promised or
predicted here. What can be engineered: a tight scope, a shareable 30-second
failure demo, a portable envelope, a published threat model, and a test suite
that a stranger can run in one command. Those are the inputs; distribution is
not. The research reports explicitly refuse to fabricate growth projections.

## Decisions frozen for v1

- One real execution per invocation (ADR-001).
- The agent's view is reconstructed from captured bytes, never from a second run.
- Unsupported shell constructs produce a refusal and no execution.
- The ledger is tamper-evident, not tamper-proof (ADR-003).
- MPL-2.0, standard library only (ADR-004).
