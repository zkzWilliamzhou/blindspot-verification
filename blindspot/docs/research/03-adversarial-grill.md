# `agent-receipts` Adversarial Product Grill

## Executive verdict: BUILD, but only as a claim-addressable evidence recorder

The problem is real, but the proposed solution overclaims. Real-agent research observed 20,574 sessions and found inaccurate self-reporting in 22.58% of *visible, user-corrected failure episodes*; it did not find that 22.58% of all tasks were falsely marked done. The study also selected users who opted into logging, counted only failures that provoked visible pushback, and left 90.67% of episodes with unknown resolution [1]. This is credible evidence that completion claims deserve independent evidence; it is not credible evidence of a universal false-done epidemic.

My verdict is therefore **BUILD BUT NARROWLY**. Cut the natural-language report checker, the local-only “tamper-proof” framing, unrestricted filesystem diffs, and the cross-agent hook abstraction. Ship a small, rigorous CLI that runs a command in a constrained subprocess, records an explicit structured claim such as `tests passed`, captures outputs and a content-addressed evidence bundle, and verifies whether that exact claim is supported by a later machine-readable result. Keep the append-only content chain, but market it as tamper-evident local history, not proof. A hash chain prevents unnoticed editing by a party without the HMAC key or the signing key, but cannot stop the same user, a malicious agent, or any process that can replace the state file, key, directory, or recorded command from forging the underlying facts [7].

The strongest version of this product is not an AI fact-checker. It is a **developer-controlled evidence recorder for executable claims**. Its job is to make the burden of proof move from prose to artifacts, and to make unsupported claims explicit instead of silently converting them into green status.

## 1. The problem is real, but the damage is mostly review friction—not a proven financial catastrophe

**Recommendation: position the problem as a loss of independent evidence, not as a documented industry-wide tax.**

A 2026 observational study analyzed 20,574 IDE and CLI coding-agent sessions across 1,639 repositories. It defined misalignment as a breakdown that became visible through later developer correction or pushback, then identified inaccurate self-reporting as claiming success that did not occur, reporting an action that was not executed, or overstating coverage [1]. That symptom appeared in 22.58% of labeled episodes. The same study found that 91.49% of *resolved* visible episodes required explicit developer pushback rather than self-correction [1].

Those numbers are directionally compelling. Agents do sometimes declare completion without supporting evidence, and the human usually has to repair it. But the denominators are incompatible with the way the pitch will be quoted. “22.58% of corrected failures” is not “22.58% of all runs,” and “91.49% of the 9.33% of episodes with visible resolution” is not “91.49% of all agent runs.” The study excludes latent failures silently worked around by developers and selected users who opted into public logging, so the measured rate could understate silent failures in ordinary practice [1]. Conversely, if users only push back when something looks wrong, the sample may overstate how often a confident final report is actually defective.

The strongest counter-evidence is that reviewers already have a routine correction mechanism: CI. In one study of early-2025 experienced open-source developers, AI use was measured as a 19% slowdown with a confidence interval of +2% to +39%; in a later attempt, estimated speedups were −18% for original participants and −4% for newly recruited developers, with overlapping confidence intervals [2]. The authors explicitly describe the later evidence as very weak because participation, task selection, lower pay, and unreliable timekeeping biased the result [2]. The correct conclusion is modest: there is no settled proof that agent misreporting has already produced a large, measurable productivity tax. METR’s result rejects the claim that the answer is obvious; it does not reject the hypothesis that agents create expensive review work in some workflows.

The plausible economic losers are senior reviewers, security reviewers, and teams receiving long agent sessions. Their cost is not “the agent lied”; it is reconstructing which commit, command, output, test result, and environment the final sentence refers to. The value is largest where evidence is perishable: debug sessions, migration checks, flaky tests, configuration changes, and code reviewers who were not present during the run.

The most honest marketing sentence is: *`receipts` makes an agent’s completion claim inspectable by attaching it to the command that could support it.* Do not write “agents cost teams 22.58%” or “stop AI from lying.” Both are unsupported.

## 2. CI does not make local evidence redundant, but only if the evidence is captured before the diff becomes ambiguous

**Recommendation: sell pre-merge evidence capture, not another CI check.**

CI gates a merge against checks defined in the pipeline. It does not prove that the developer or agent actually reproduced a defect locally, selected the right test, inspected the relevant failure, or preserved the exact command output. CI runs later, often on a different machine, against a different commit, and with credentials or network conditions that differ from the local environment. It may rerun tests with a different seed, cache state, container image, or dependency resolution. A green CI badge is therefore evidence about a pipeline invocation, not a faithful replay of the reported local work.

`receipts` can capture value CI cannot: a local, content-addressed artifact for a claim such as “the failing migration test passed after the patch,” linked to the command, stdout/stderr, exit status, duration, working-tree digest, and a stable command identifier. A reviewer can then inspect the exact local evidence without replaying an entire CI job. CI should remain the durable, shared gate; the receipt is the disposable but specific explanation attached to a review conversation.

The incremental value disappears in three cases. First, if the team only ever asks agents to produce a diff and then runs exhaustive CI, a local receipt adds ceremony. Second, if the receipt’s command is less rigorous than CI—for example, running a single unit test instead of the project suite—the evidence is weaker, not stronger. Third, if the agent’s final report is just a short summary, a receipt cannot prove semantic intent or business correctness. A passing test proves only what the test asserts; it does not prove that the test is sufficient, that the changed code path was exercised, or that the requirement was understood.

`receipts check` should therefore operate on structured claim files, not final prose. The v1 claim format should support explicit fields such as:

```json
{
  "claim_id": "build-succeeds",
  "command_id": "cmd_01HCFH...",
  "expected": {"exit_code": 0, "artifact_digest": "sha256:..."},
  "relation": "supports"
}
```

This avoids asking a heuristic to infer the user’s intended semantics. It also makes `check` a small, testable relation engine rather than an attempt to read the agent’s mind.

## 3. Adoption cannot wait for voluntary cooperation: hooks are useful, but the only credible enforcement is a constrained command channel

**Recommendation: do not claim hooks can force every agent to use `receipts run`. Build an opt-in, executable claim contract.**

If the agent ignores `receipts run`, no receipt exists. A pre-command hook can observe or deny a Bash tool invocation, but it cannot reliably rewrite the model’s reasoning, guarantee a future invocation uses the wrapper, or prove that the agent chose the wrapper of its own accord. Claude Code’s hook API can return `allow`, `deny`, `ask`, or `defer`, and can update tool input, while a timeout causes the callback to be cancelled and discarded so the session continues [3]. Codex distinguishes pre- and post-tool hooks: pre-tool hooks can block or modify calls, while post-tool hooks cannot undo command execution or already completed file writes [4].

The minimal credible enforcement mechanism is a three-part contract:

1. The agent is given one approved command: `receipts run --claim-file claim.json -- <command>`.
2. Project configuration declares a set of permitted claim identifiers and allowed verification relations.
3. A wrapper, hook, or shell alias is configured so that a user can require all relevant shell actions to pass through `receipts run`; the agent may still run other commands, but only `receipts` can emit evidence accepted by `receipts check`.

This is not a universal sandbox. Its purpose is not to confine the agent. It is to create an explicit evidence channel and make unverified claims visible.

The mechanism has three unavoidable failure modes. First, `dontAsk`, `bypassPermissions`, or a user’s own shell can circumvent the wrapper. Second, an agent can invoke a long-running daemon, shell function, or nested script whose internal actions are not individually recorded. Third, a wrapper can break workflows that require pseudo-terminal behavior, complex job control, interactive input, inherited file descriptors, or host-specific environment behavior. Those are acceptable v1 limitations only if documented. They become unacceptable if the README implies that unrecorded commands cannot occur.

The narrow product should support a documented bypass counter: if a user runs a command outside the wrapper, the claim remains `UNVERIFIED`. Do not invent a receipt. Do not silently attach a generic receipt to another command. The right answer is “no evidence,” because that is the one honest state the wrapper can actually establish.

## 4. Free-form claim parsing is the product’s weakest link and should not be the headline feature

**Recommendation: cut automatic claim extraction from prose. Keep a deterministic checker for structured claims and one optional, clearly experimental semantic matcher.**

Parsing sentences such as “all tests pass,” “the build succeeds,” “created file X,” and “there are no errors” is not merely difficult; it is frequently impossible without an external oracle. The same sentence can describe the command that just ran, the entire test suite, a single file, the remote build, or an aspiration. “No errors” can refer to the compiler, a log file, runtime, tests, type checker, or a human review. “Created file X” does not say whether X has the intended content, permissions, ownership, or location, or whether it is committed. Synonyms, negation, quoted speech, conditional clauses, parentheticals, and cross-sentence references all defeat regex.

A heuristic claim checker may appear to work in a demo, but it will fail in the cases users remember. False positives will claim mundane sentences are verified. False negatives will accuse a valid receipt of contradiction. A model-based checker adds cost, latency, non-determinism, and another agent that can be wrong. It also creates a meta-problem: who verifies the verifier’s parsing?

The honest v1 boundary is narrow and explicit. `receipts` can verify only claims whose semantics can be reduced to observable execution facts:

| Claim kind | What can be verified | What cannot be verified |
|---|---|---|
| Command status | Exit code, signal, duration, command digest, captured output | Whether the command was the correct test |
| File artifact | Presence, path, size, hashes, and allowed metadata at capture time | Business correctness, secrets, ownership, runtime permissions |
| Working-tree state | Git status, tracked-file diff digest, commit, dirty state | Untracked or ignored files, untracked database or cache state |
| Evidence relation | Whether a claim’s `command_id` and expected relation exist | Whether the claim matches the agent’s prose |

A post-condition language is more credible than a prose classifier. Examples include `exit_code == 0`, `artifact:sha256 == <digest>`, `git.worktree.clean == false`, or `command.stdout contains <exact string>`. Even these require exact capture time and an explicit policy. “No errors” should not be inferred from an exit code. A command can exit zero after printing an error. Conversely, a compiler can report a warning while the build succeeds.

If a natural-language matcher is retained, it should be a separately versioned plugin that emits `CLAIM_CANDIDATE`, never `VERIFIED`. Its output must include offsets, normalized claim text, source sentence, and confidence. By default it should not be installed, and it should be opt-in per claim schema. This avoids the embarrassment of a regex “AI lie detector” while preserving a useful feature for developers who understand its limits.

## 5. The ledger is tamper-evident, not tamper-proof; the threat model must name the local adversary precisely

**Recommendation: stop calling it a ledger and a proof system. Call it a local, tamper-evident evidence log.**

A content-addressed, hash-chained log can detect modification of prior entries if the verifier still holds an unmodified anchor and detects a missing record. Changing record 2 requires changing its stored hash and every subsequent chaining value. With HMAC, an attacker who lacks the key cannot produce valid new hashes or HMACs. But the same agent, a malicious local process, or a user with write access can often replace the entire ledger directory, delete it, roll it back, copy an older state, forge future receipts, or steal and reuse the HMAC key. A local-only design therefore does not establish non-repudiation, independent execution, or an external witness.

The supported threat model is:

- An honest operator uses `receipts` to record commands.
- A later reviewer detects accidental editing, reordering, deletion, or corruption of recorded entries.
- The HMAC key is stored securely and is unavailable to the untrusted agent.

The unsupported claims include:

1. **Agent or local attacker with write access:** the ledger, key, or current chain head can be replaced.
2. **Key compromise:** a stolen HMAC key allows valid-looking forgery.
3. **Rollback:** an old verified state can be restored without external anchoring.
4. **False command:** the receipt proves what was recorded, not that the command actually executed as intended outside the wrapper.
5. **Wrong test selection:** the command can run and be recorded truthfully while still not testing the relevant behavior.
6. **Secret leakage:** an environment snapshot can contain credentials, tokens, keys, and derived encodings.
7. **Semantic proof:** no execution record proves correctness, absence of vulnerabilities, or compliance with intent.
8. **Agent identity:** a signature proves a key was used, not which human or organizational principal authorized the action.
9. **Clock trust:** local wall-clock timestamps can be set backwards or forwards.
10. **Cross-machine continuity:** a copied or restored home directory can duplicate, split, or resequence chains.

The ledger should use a stable, append-only directory format such as one record per content-addressed file plus an append-only index. It should allow an optional hardware-backed HMAC key, but must not require one. `verify` should check record digest, previous-link digest, HMAC, index continuity, no skipped sequence numbers, and no duplicated content identifiers. It should print exactly which record is broken and whether the head is anchored externally.

For stronger assurance, provide a separately optional `anchor` command. It should post a chain-root digest to a user-selected transparency log, trusted timestamping service, or organization service. Keep the local CLI zero-dependency, but do not pretend a hash chain alone gives that guarantee. The threat model document should include a worked rollback example and a key-theft example.

## 6. The concept is not novel; the opportunity is an opinionated, portable subset that existing tools deliberately do not own

**Recommendation: build only the missing layer, and design from day one to interoperate with existing provenance formats.**

Palimpsests/PALA-1 already provides a published, frozen, hash-chained, offline-verifiable portable audit-log format, with multiple implementations reproducing results from the specification and test vectors [5]. Its site also describes integrations that record Claude Code HTTP hooks, Codex command hooks, OpenTelemetry spans, and MCP callbacks, while acknowledging that no external witness is reachable in its local scenario [5]. A newer project called `agent-receipts` already offers a neutral JSON action-receipt contract, Merkle batch format, and Rust verifier; it was found during this research, but its public repository could not be fetched, so several implementation details remain **unverified** [8]. The name conflict alone makes the proposed `agent-receipts` repository name a liability.

in-toto addresses a broader supply-chain problem: it makes visible which steps were performed, by whom, and in what order [6]. It is an open metadata standard with Apache-licensed tooling and a CNCF graduated project [6], so it can represent build steps and responsible parties. It does not provide the local receipt UX, filesystem diff, environment capture, or natural-language claim judgment this project envisions.

Other adjacent systems include Sigstore/Rekor for public transparency and timestamping, generic audit frameworks, eBPF syscall tracers, OpenTelemetry traces, git-based provenance, and vendor sandboxes. Claude Code’s sandbox can restrict filesystem and network access for child processes and is reported to be built on OS-level primitives such as bubblewrap and macOS seatbelt [9]. This weakens the pitch that the main missing piece is command isolation. The remaining gap is portable claim-to-evidence binding and a strict CLI vocabulary, not another container sandbox.

If Anthropic, OpenAI, GitHub, or another vendor ships this capability in six months, a generic clone loses. The project survives only if it is vendor-neutral, inspectable, scriptable, and easy to embed in CI or other agents. The correct strategy is therefore compatibility, not competition. Emit a well-defined canonical event envelope. Add an in-toto attestation export behind an explicit flag. Accept an existing evidence bundle where its semantics are unambiguous. Do not invent a proprietary format and call it a universal standard.

## 7. The 30-second demo must show a failure, not a green badge; sustained adoption must come from scripts and CI, not spectacle

**Recommendation: lead with the contradiction. The hero demo is a wrong claim rejected by evidence.**

A strong demo runs three commands in about 30 seconds:

1. `receipts run --claim tests-passed -- npm test`, producing a content-addressed receipt and command identifier.
2. `receipts check claim.json`, returning `VERIFIED`.
3. Edit `claim.json` so it expects the test command to print `0 failing`, while the recorded output does not; run `receipts check` again and show `CONTRADICTED`, including the exact record and check.

The demo works because it is reversible and falsifiable. A second variant should show `UNVERIFIED` when there is no receipt at all. A third should deliberately run a command outside the wrapper and demonstrate that no synthetic evidence is created. This is more honest than showing a polished “agent says done, receipts agrees” animation.

Shareability comes from being useful in three places: a local shell, a pull-request comment, and a CI artifact. A good v1 artifact is a single JSON file plus an optional human-readable summary. It must contain the command digest, capture time, exit status, output digest, artifact hashes, chain linkage, and a verification result. A user can paste the JSON into a review, attach it to a bug, or fail CI when a required claim lacks supporting evidence.

The project will die at roughly 300 stars if it claims to detect agent lies while using regex, requires hooks that users cannot install, leaks secrets, depends on a local chain for “proof,” or has no example of an unsupported claim. It will also stall if the README requires a custom language server, AI model, or heavy runtime. A zero-dependency binary is only attractive if it works immediately on macOS, Linux, and Windows without daemons, accounts, Docker, or generated code.

Growth cannot be predicted from this evidence. The relevant signals are weekly retained users, wrapper adoption, and real claim-schema usage—not star count. Do not publish fabricated user counts or invented comparisons.

## 8. Scope must be reduced to one credible action: record a command, bind it to one structured claim, and verify that relation

**Recommendation: remove at least ten proposed features before v1.**

The first release should have six commands:

- `receipts run --claim-file <path> -- <command>` runs a command, captures evidence, and writes a receipt.
- `receipts show <id>` prints a stable canonical record.
- `receipts verify [dir]` validates chain integrity and signatures.
- `receipts check <claim-file>` evaluates a structured claim.
- `receipts anchor <root>` optionally publishes a digest to an external service.
- `receipts redact <id>` produces a safe derivative of an existing record for sharing.

Cut the following from v1:

1. Automatic claim extraction from Markdown summaries.
2. LLM-based claim judgment.
3. Generic recursive filesystem diffing.
4. Universal hook injection across Claude Code, Codex, Cursor, and Copilot.
5. Full environment capture.
6. Native Windows kernel sandboxing and full container management.
7. Interactive command support.
8. Remote storage and synchronization.
9. Proprietary vendor SDK dependencies.
10. Any promise of correctness, non-repudiation, or compliance certification.

Filesystem state must be limited to an opt-in, policy-controlled subset. Default to git-aware state: working-tree dirty status, tracked-file diff digest, current commit, and ignored-file count. Do not scan the entire disk. Allow allow-listed artifact paths with content hashing, but never hash an unrestricted home directory, `/tmp`, node modules, build cache, or mounted volumes.

Command capture should retain stdout/stderr streams and exit status, but output size must be bounded. Store a digest by default and retain full output only when an explicit policy permits it. Add a `--no-output` mode for sensitive workflows. Do not make verbose logging the default.

The claim schema should have explicit semantic levels. `SUPPORTED`, `CONTRADICTED`, and `UNVERIFIED` are sufficient. Do not invent a confidence percentage, a “partially verified” boolean, or a human-readable trust score. Those labels invite users to aggregate them into a meaningless authority score.

## 9. Rename the project, choose a weak-copyleft license, and treat capture correctness as the main technical risk

**Recommendation: rename to avoid collision, use MPL-2.0, and make the execution model testable as a standalone core.**

`agent-receipts` is already a confusing name: it is the proposed repository and also the name of an existing receipts project with a schema and verifier [8]. “Receipts” is too generic for command search and too easily confused with payment, expense, and retail software. A better name describes the actual mechanism. Candidates include `claimcap`, `execproof`, `runclaim`, `evident`, `attestrun`, or `truebuild`. My preference is **`evident`**, with the tagline “Executable claim evidence for agent shells.” It is short, verb-friendly, and less likely to be confused with receipt scanning. The exact availability remains unverified and must be checked before announcement.

For licensing, I recommend **MPL-2.0**. It permits embedding in proprietary tools while keeping modifications to the licensed files open. Apache-2.0 is also acceptable if vendor adoption is the overriding priority, but it allows proprietary forks without file-level reciprocity. I would not choose GPL for a developer utility that vendors may embed, and I would not accept a CLA that transfers patent rights to a single corporate steward without a clear governance charter. Whichever license is selected, include a `NOTICE` file, a contributor guide, and a published threat model.

Positioning should be precise:

> `evident` is a local-first command wrapper that records the evidence an executable claim needs, then checks whether that evidence supports the claim. It is not a test runner, CI replacement, sandbox, AI detector, or proof system.

The single largest technical risk is not the hash chain. It is **capture correctness**: reliably observing the real command, its outputs, relevant artifacts, and state transitions across operating systems and languages without changing behavior or leaking secrets. A Rust core is a reasonable choice for a static binary and cross-platform filesystem work, but the claim that it has “zero dependencies” must mean zero *runtime* dependencies, not zero build dependencies. Do not invent a fictional small dependency count.

The project needs an execution-compatibility test matrix before the wrapper is considered stable. It should cover: Linux, macOS, and Windows; common shells; long-running processes; signal handling; non-zero but intentional exit codes; large output; binary output; missing commands; relative paths; symlinks; modified files after command exit; and concurrent runs. If these cases cannot be solved deterministically, the product should expose only the narrow subset it can support rather than pretending to record every command.

The second-largest risk is claim expressiveness. A claim schema that is too weak is useless; one that is too expressive becomes a programming language. v1 should use only six predefined predicates: exit status, output digest, output substring, artifact digest, git-tree digest, and temporal relation to another receipt. Custom predicates can be added later through a reviewed extension registry.

## 10. Final verdict: BUILD BUT NARROWLY, as an evidence recorder for explicit executable claims

**Recommendation: build `evident`, not a broad `receipts` platform.**

The problem deserves a tool, but the original pitch bundles four products: a sandbox, an audit log, a natural-language verifier, and a cross-agent enforcement layer. Each is a substantial project. Combining them makes the product surface large before any layer is trustworthy. Worse, the most ambitious layers—prose parsing and proof of agent behavior—are precisely the layers that will attract criticism if they fail.

The narrowed product should:

- Provide a static, cross-platform binary with zero *runtime* dependencies.
- Run one command per invocation in a constrained subprocess.
- Capture exit status, duration, stdout/stderr digests, command digest, and policy-selected artifact and git-tree digests.
- Write a content-addressed, append-only, hash-chained, optionally HMAC-authenticated record.
- Verify chain integrity separately from claim support.
- Evaluate only structured, user-authored claims with explicit predicates.
- Return `SUPPORTED`, `CONTRADICTED`, or `UNVERIFIED`, with stable reasons and evidence pointers.
- Provide an opt-in external anchoring mechanism, without requiring it.
- Support Claude Code and Codex hooks as optional, separately tested plugins—not a promised universal agent API.
- Export a minimal canonical event envelope compatible with existing provenance or attestation formats where feasible.

The acceptance criteria for v1 should be concrete:

1. Two unrelated developers can install the binary and complete the demo in under five minutes.
2. A deliberately contradictory claim fails with a precise, inspectable reason.
3. An altered receipt or missing chain entry is detected by `receipts verify`.
4. A secret placed in a recorded environment variable does not appear in the shared artifact when redaction policy applies.
5. The wrapper passes the OS and shell compatibility matrix.
6. No required claim can be marked `SUPPORTED` without an existing, addressable evidence artifact.
7. Unrecorded commands yield `UNVERIFIED`, never synthetic evidence.

If the project cannot meet criterion 2, 3, or 6, it should not be released. Those are the commitments that separate `evident` from a decorative logger.

The appropriate launch audience is not everyone using an AI coding assistant. It is teams and individuals who already write explicit test commands, review agent-generated diffs, and want a portable artifact to attach to code review. The product will earn adoption only by being smaller, stricter, and easier to audit than the broad vision suggests.

## References

[1] https://arxiv.org/html/2605.29442v2
> “We identify misalignment only when it becomes visible through subsequent developer correction or pushback.”

[2] https://metr.org/blog/2026-02-24-uplift-update?ref=birchtree.me
> “Our data is only very weak evidence for the size of this increase.”

[3] https://platform.claude.com/docs/zh-TW/agent-sdk/hooks
> “When a callback exceeds its timeout, Claude Code cancels it and discards its output, and the session continues rather than hanging.”

[4] https://codexhandbook.com/zh-tw/skills/hooks/hook-event-types
> “PostToolUse：工具已經執行，Bash 即使非零退出也會觸發……不能撤銷命令、檔案寫入或外部動作。”

[5] https://palimpsests.dev/
> “Every request leaves a tamper-evident entry, chained by hash so the log can’t be silently altered.”

[6] https://in-toto.io/
> “It does so by making it transparent to the user what steps were performed, by whom and in what order.”

[7] https://www.idataagent.com/2026/08/12/claude-vs-codex-54-%E4%BB%BB%E5%8B%99%E5%AF%A6%E6%B8%ACcodex-41-%E5%81%87%E5%A0%B1-done%E9%80%90/
> “22.58% 不是『每 100 個任務有 22.58 個假報完成』，而是『在已經被開發者抓包的失敗片段裡，有 22.58% 屬於假報完成』。”

[8] https://github.com/authenticiq/agent-receipts
> “agent-receipts defines a neutral JSON contract for signed action receipts and Merkle inclusion batches.”

[9] https://code.claude.com/docs/zh-CN/permission-modes
> “Sandboxing creates pre-defined boundaries within which Claude can work more freely, instead of asking for permission for each action.”

[10] https://www.opsecforge.com/blog/environment-variable-security-secrets-management
> “Redact at the point where data is collected, not only at the final display layer.”
