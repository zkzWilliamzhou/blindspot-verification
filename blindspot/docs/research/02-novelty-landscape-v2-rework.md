# Agent Verification Novelty Landscape, Reworked: Observation Integrity and Claim Freshness

## Executive summary: the defensible opening is a claim-to-observation contract, not a general evidence platform

The correct conclusion is narrower than “no verified tool owns the claim-to-evidence contract,” and also narrower than “the space is empty.” The field is crowded with partially overlapping functions: alibi tests counterfactual test meaningfulness; Reverify verifies structured binary claims; CodeVetter binds checks to an agent revision; anti-fake-complete grades evidence level; honestly checks assertions against an alleged test run and blocks selected output-hiding commands; PALA-1 and agent-receipts standardize durable, externally verifiable action records. The first review’s error was not only omission; it was overgeneralization from incomplete coverage.

The strongest remaining primary function is therefore not a generic audit log, receipt, or verifier. It is **the claim-to-observation contract**: capture exactly what an agent observed, execute the same command in a clean and independently controlled observation channel, determine whether the observation faithfully represents execution, and report a signed delta rather than merely blocking risky syntax. Candidate A is the less occupied and more defensible of the two proposed slices. Candidate B has stronger conceptual novelty but more direct adjacent machinery in Bazel, Nix, GUAC, CocoIndex, ageval, and incremental indexing.

Direct searches for tools that detect `|| true`, `; true`, `set +e`, ANSI-hidden failures, output truncation, context-window clipping, or “the agent saw only the last line”—and that then re-execute the command cleanly and report an exact delta—did not return a tool with that primary function. This is a **negative search result, not proof of global absence**. The strongest honest limitation is unavoidable: no finite web search can establish that an unindexed, private, pre-release, renamed, or future tool does not exist.

## 1. The first conclusion failed because it treated incomplete coverage as a claim-to-evidence gap

The earlier “no verified tool” conclusion collapsed several different questions into one. A tool may lack a universal evidence standard while still owning a narrower primary function. Another may standardize transport and offline verification without deciding whether a test was meaningful. A third may guard a reply without measuring the faithfulness of the observation on which the reply was based. These are overlapping concerns, but they are not interchangeable. A correct novelty assessment must distinguish what a tool observes, what it verifies, when it intervenes, and what contract its output establishes.

**The space is crowded, but it is crowded with adjacent specialties rather than one general claim-to-evidence owner.** Six of the supplied projects can be verified from public secondary descriptions as distinct specializations. alibi asks whether a new test distinguishes old from new behavior. Reverify returns a three-valued verdict for structured binary claims and retains verified facts locally. CodeVetter binds verification to an exact agent revision and emits a fail-closed evidence bundle. anti-fake-complete classifies evidence levels and refuses to call evidence “verified” when it falls below the required bar. honestly checks an agent’s completion assertion against a claimed test run and intercepts selected evasive commands. PALA-1 and agent-receipts move the focus upstream to durable, independently checkable records of action.

The supplied descriptions for some of these repositories could not be confirmed from canonical project pages in this research pass. Their functions are reported here as supplied, not as independently verified source-code facts. In particular, repository URLs, exact licenses, implementation details, release status, and production deployments remain unverified for alibi, Reverify, CodeVetter, anti-fake-complete, PALA-1, and agent-receipts. Those limits do not erase the supplied functional boundaries; they prevent treating them as settled primary-source evidence.

| Project | Supplied primary function | Defensible boundary | Verification status in this review |
|---|---|---|---|
| BOTIROFF-D/alibi | Tests whether a new test fails on old code | Counterfactual test meaningfulness, not observation fidelity | Supplied description only; repository and license unverified |
| Reverify | Returns VERIFIED, REFUTED, or INCONCLUSIVE for structured PE/ELF/Mach-O claims | Claim domain is binaries; local ledger recovers verified facts after reset | Supplied description only; repository and CLI/MCP surface unverified |
| CodeVetter | Verifies an agent’s changes against the exact revision it produced | Task-bound, execution-backed checks; fail-closed evidence bundle | Supplied description only; revision binding and bundle schema unverified |
| ardianwn/anti-fake-complete | Classifies evidence across levels L0–L6 | Validator rejects claims below the required evidence level | Supplied description only; level definitions and validator unverified |
| honestly | Blocks evasive test commands and checks assertions | Reply-time gate plus selected command interception, not clean re-execution | Behavior partially described in a public write-up, but repository metadata unverified |
| Palimpsests/PALA-1 | Defines a hash-chained, offline-verifiable audit-log format | Portable format and integrations rather than claim semantics | Supplied description only; specification, implementations, and test vectors unverified |
| authenticiq/agent-receipts | Defines neutral JSON action receipts and Merkle inclusion batches | Portable receipt contract with a Rust verifier, not a verdict domain | Supplied description only; schemas, verifier, and interop unverified |

The implication is methodological: novelty must be stated at the level of the **claim lifecycle**, not at the level of “verification” in general. A test-result format does not solve counterfactual test quality. A signed receipt does not prove that the observer saw the relevant part of the output. A revision-bound evidence bundle does not automatically determine that a later file change has invalidated an older claim. Conversely, none of those tools is rendered useless by the existence of the others.

## 2. The two strongest gaps are at opposite ends of the evidence lifecycle

The remaining design space is easiest to see as two separate contracts. Candidate A intervenes at the boundary between execution and observation: it does not ask whether the command was authorized, whether the test suite was comprehensive, or whether the receipt is durably signed. It asks whether the agent’s observed result faithfully represents what actually happened. Candidate B intervenes after verification: it assumes that a claim was once valid and asks which current claims remain valid after their inputs change.

**Candidate A is a fidelity layer for the observation channel; candidate B is a provenance and invalidation layer for conclusions.** They share a concern with evidence quality, but their failure modes and intervention points differ. A may execute correctly while hiding the failure from the agent; B may faithfully record a result that later becomes semantically stale. An implementation could combine them, but combining them would not remove the need to specify which contract is primary.

### Candidate A: observation-channel integrity

A deploy this function as a shell wrapper or pre-tool hook that records the original command, its parsed transformation graph, and the full raw standard streams. It would construct a clean observation channel with a fresh environment, no interactive pager, no inherited shell aliases, explicit stream capture, and deterministic handling of output limits. It would rerun the same effective command, then compare the raw complete result with the result the agent actually received.

Its verdict would not be “safe” or “unsafe.” It would state whether the observation was complete, whether the observed exit status matched the raw exit status, whether suppressed standard error changed the interpretation, whether a pipe or redirection destroyed relevant terminal output, whether a timeout or context truncation removed information, and whether a command executed after the claimed test changed the relevant state. The report would include the exact delta: missing lines, hidden ANSI sequences, exit-code laundering, side effects, and any state change between the two observations.

### Candidate B: evidence-staleness graph

A deploy this function as a local store of verification claims. Each claim would identify its predicate, evidence artifacts, effective command, captured exit status, execution environment, and a content-addressed input set. The input set would include file blobs, tree hashes, resolved dependencies, tool versions, configuration, and environment variables selected by a policy.

The graph would maintain explicit relationships among source files, derived artifacts, checks, claims, and conclusions. When a tracked input digest changes, the system would mark affected claims stale rather than delete them. It would then rerun only the claims whose inputs changed or whose ancestors changed, using content hashes and a dirty set instead of naive path matching. The final output would be a freshness explanation such as “claim 7 depended on file A; file A changed; claims 3, 7, and 11 are stale; 2, 5, and 8 remain valid.”

### The two functions solve different failures

| Property | Candidate A | Candidate B |
|---|---|---|
| Primary question | Did the agent observe what actually happened? | Does a previously valid claim remain valid? |
| Unit of analysis | Command, standard streams, exit status, observation boundary | Claim, predicate, artifact digests, dependency graph |
| Main intervention | Before or during command observation | After verification, on file or environment change |
| Typical failure detected | `pytest \| tail -1`, `\| head`, `2>/dev/null`, `; true`, context truncation | “12 claims were verified last week; one input changed; 9 are stale” |
| Typical non-goal | Test quality, sandbox policy, receipt signing | Raw output fidelity, test-quality judgment |
| Closest non-owner | honestly, RTK, TACO, harness truncation controls | Bazel, Nix, GUAC, CocoIndex, ageval |
| Strongest residual question | What counts as an observation-preserving transformation? | Which claims should be invalidated by a semantic dependency, not merely a hash change? |

The distinction matters because both gaps can exist in a session that already has receipts, hooks, and sandboxing. A receipt can faithfully record a misleading observation. A sandbox can permit a command while the agent sees only its tail. A comprehensive test report can remain cryptographically intact after the source it describes has changed. Those are not contradictions; they are separate integrity boundaries.

## 3. Candidate A is less occupied because observation fidelity is narrower than general command governance

Candidate A has fewer direct owners, but it is still not a greenfield. honestly is the closest existing tool; RTK and TACO are adjacent because they transform the observation itself; Claude Code hooks and sandboxing provide surrounding controls. None of them was found to make observation fidelity its primary contract.

**honestly is the closest incumbent, but it does not own candidate A.** According to a public write-up, honestly inspects the pending reply for assertions such as “tests passed,” checks whether a test, build, or run actually occurred after the last code change, and looks for a supporting summary line. It also intercepts selected commands: `pytest | head`, `| grep -c`, `| wc`, and `go test ./... | tail` are rejected because they can hide the relevant result, while `pytest | tail` is permitted because it retains the summary line. The write-up also reports that its author replayed 73 historically intercepted commands and 219 sessions; these are implementation reports, not independent evaluations of correctness or completeness.

That is materially different from candidate A. honestly evaluates whether an assertion appears to be supported and whether selected command patterns create obvious risk. Candidate A would preserve the full raw result, record exactly what the agent saw, create a clean rerun channel, compare the two observations, and report a delta. honestly’s allowance of `pytest | tail` illustrates the difference: retaining the final summary line may be acceptable for one checking policy, but it is not equivalent to proving that no earlier failure, warning, side effect, or state change was hidden.

![Evidence陈旧性图比观察通道完整性留下更少的近端重叠](/data/workspace/dr:rework-novelty-landscape/fig_adjacent_overlap.png)
*Figure 1: Evidence staleness graph (B) has stronger direct adjacent machinery than observation-channel integrity (A). Data source: honestly, RTK, TACO, Claude Code hooks/sandbox, Bazel, Nix, GUAC, CocoIndex, and ageval [7]–[20]. Counts are qualitative adjacency indicators, not a market share or feature-completeness measurement.*

### RTK and TACO transform output; they do not verify fidelity

RTK sits between an agent and the shell and filters, aggregates, truncates, and deduplicates terminal output before it reaches model context. A write-up describes four mechanisms—intelligent filtering, grouping, truncation, and deduplication—and states that an auto-rewrite hook can intercept Bash calls and convert them into RTK-wrapped calls. The same source says built-in Read, Grep, and Glob tools are not rewritten through that Bash hook. RTK’s stated goal is token-efficient observation, not faithful preservation of every execution signal. Its truncation is therefore an observation-risk mechanism that candidate A would need to treat as untrusted by default.

TACO takes a more adaptive approach. It compresses terminal output through rules composed of trigger conditions, retention patterns, and removal patterns; it then refines those rules within a task and promotes useful rules to a global pool. Public material reports that it detects over-compression signals such as repeated full-output requests, repeated commands, or behavior suggesting missing information. That is closer to candidate A than a static blocklist because it observes the consequences of information loss. Nevertheless, TACO’s primary function remains compression and adaptive context management. It does not establish a claim-to-observation contract, preserve the raw result as the canonical evidence source, or emit a delta proving what the agent failed to observe.

### Hooks and sandboxing are controls, not observation contracts

Claude Code hooks can intercept Bash execution and stop a command before it runs, while its sandbox can constrain filesystem and network access. These mechanisms are background infrastructure for candidate A, not substitutes for it. A hook can enforce a policy; a sandbox can restrict what a command may affect; neither necessarily records what the agent ultimately observed, compares it with a clean execution, or proves that a permissible command produced a permissible observation.

This distinction also limits what candidate A can promise. A clean re-execution may still differ from the original because of time, network state, randomness, concurrency, secrets, or external services. A robust design must therefore distinguish **observable delta** from **nonce or environment delta**, and it should not claim equivalence when the second execution has different inputs. The contract is strongest for deterministic local commands over immutable inputs.

## 4. Candidate B is less occupied than build-system incrementality, but not by as much

Candidate B has a stronger conceptual boundary than simply “rerun tests when files change.” Its unit is not a build target but a verified claim; its output is not merely a new build graph but a freshness explanation that survives context reset and supports partial re-verification. Still, the adjacent space already contains mature dependency-tracked execution, content-addressed builds, software-metadata graphs, incremental indexers, and trace viewers.

**Bazel and Nix cover most of the mechanism but not the claim semantics.** Bazel tracks action inputs through content-addressed file systems, propagates invalidation through the action graph, and skips actions whose inputs are unchanged. Nix derives build outputs from content-addressed derivations and can avoid rebuilding when the derivation and inputs are unchanged. These systems provide exactly the machinery needed to answer “which work must be redone?” They do not, by default, expose a local vocabulary of verification claims such as “this test implies that property P holds for revision R,” bind that claim to a specific evidence bundle, or explain why a semantically related but hash-distinct input should or should not invalidate the claim.

**GUAC and CocoIndex provide graph and incremental-update machinery but different contracts.** GUAC aggregates software-supply-chain metadata—artifacts, vulnerabilities, repositories, dependencies, and builders—into a queryable graph. CocoIndex and similar incremental engines recompute only the materialized results affected by source changes. ageval records agent input, tool calls, terminal output, and model replies, and can reproduce a single failed task. None of these was shown in this review to maintain a local truth graph whose primary object is a verification claim, whose edges are evidence dependencies, and whose output is a claim-level freshness explanation.

That distinction creates a meaningful narrow function: a local graph that materializes the evidence dependency of each claim, records the content digests and execution context that made it valid, marks descendants stale after a tracked input changes, and re-verifies only those claims through their original or equivalent procedures. It would differ from a build system because its vertex semantics are epistemic; from GUAC because its scope is local claim freshness rather than aggregated supply-chain metadata; and from an audit log because its core operation is selective invalidation rather than durable recording.

The residual difficulty is not storage. It is **dependency discovery**. A cryptographic change in one file does not necessarily mean that every claim touching that file should be discarded. A semantically irrelevant comment may change a digest without changing a claim’s truth conditions. Conversely, a new test file, environment variable, or dependency-resolution difference may affect a claim even when none of its previously tracked source blobs changed. Candidate B must therefore combine cryptographic invalidation with a declared dependency policy. Without that policy, it risks either false staleness from irrelevant byte changes or false persistence from dependencies it failed to model.

## 5. Direct laundering and truncation searches support a null result, not a proof of nonexistence

The requested direct searches covered exit-code laundering, double-pipe `true`, `; true`, `set +e`, ANSI-hidden failures, `pytest | head` or `tail`, output truncation, context limits, and “the agent saw only the last line.” The results establish overlap but not a direct owner.

**No retrieved tool makes observation-channel fidelity its primary contract.** honestly rejects selected output-hiding command forms and inspects completion assertions. RTK deliberately compresses terminal output. TACO learns adaptive compression and can detect some over-compression signals. Claude Code hooks can intercept commands, while its sandbox constrains execution. Tencent’s Agent Observability platform can flag output truncation, tool timeouts, and parameter anomalies, but it is an observability platform rather than an agent-side clean-rerun wrapper. None of these tools was shown to re-execute the agent’s command in a clean channel, preserve both the agent-observed and raw-complete outputs, and issue a delta verdict.

| Searched failure mode | Nearest existing behavior | What remains unowned |
|---|---|---|
| `pytest \| head`, `\| grep -c`, `\| wc`, `tail` | honestly rejects selected forms; `pytest \| tail` is allowed | General transformation inference and clean re-execution delta |
| `cmd \|\| true`, `; true`, `set +e` | No dedicated tool returned | Exit-code-laundering detector tied to observed versus raw status |
| `2>/dev/null` and hidden standard error | RTK filters low-value output; harnesses may capture or drop streams | Explicit comparison of observed streams with complete captured streams |
| ANSI-hidden failures | No dedicated tool returned | Decoded terminal semantics compared with raw output |
| Context-window or harness truncation | TACO, RTK, and Tencent observability address related problems | Preservation of the full raw artifact and provenance of the presented excerpt |
| “Agent saw only the last line” | honestly checks whether the reply is supported by a run summary | Direct recording of the observation presented to the model and proof of omitted lines |

The negative result has three limits. First, search engines do not expose every private repository, unpublished package, or local script. Second, a project may implement this behavior under a generic name such as “shell guard,” “agent proxy,” or “terminal wrapper.” Third, a harness may capture complete output while presenting only part of it to the model; such a tool could theoretically reconstruct the delta, but this review found no tool whose primary exposed contract is that reconstruction.

The appropriate conclusion is therefore: **the requested functionality appears unowned at the level of directly returned public tools, with honestly as the strongest incumbent; absolute absence cannot be proven.** A project claiming novelty should use a differentiator test. If a tool blocks commands, compresses output, records traces, or checks assertion wording, it is not yet candidate A. If it cannot state exactly what the agent observed, what the clean channel produced, and which missing signal changes the conclusion, it does not own the proposed primary function.

## 6. Candidate A is the better near-term build; candidate B is the stronger research program

Candidate A should be preferred if the objective is a near-term, narrowly scoped, locally runnable tool with a measurable correctness contract. Its threat model is concrete, its instrumentation point is clear, and a prototype can use command parsing, complete stream capture, a clean rerun environment, and delta reporting. Candidate B is the more valuable research program but requires harder semantic decisions about dependencies, claim identity, and incremental verification.

**Candidate A has the better ratio of unmet need to engineering risk.** The exact failure modes are inspectable: compare the exit status returned to the agent with the raw exit status; compare the raw standard output and standard error with the text presented to the model; detect pipes, redirects, command chaining, background execution, pagers, and context excerpts; and rerun the command in a fresh channel. The output can be unit-tested with synthetic shell traces. The main research risk is defining which differences matter, not whether the comparison can be performed.

**Candidate B has greater architectural novelty but weaker immediate boundary control.** A local store can easily retain content digests and trigger rebuilds when tracked hashes change. The difficult case is a dependency that changes without changing any file already in the graph: a compiler upgrade, environment variable, clock, network resource, generated artifact, or test-order effect. If the graph does not model those edges, it may falsely preserve stale claims. Candidate B therefore requires an explicit policy boundary—for example, “hash all declared inputs or mark the claim conditionally verified”—rather than an appeal to generic incrementality.

| Criterion | Candidate A | Candidate B |
|---|---|---|
| Size of adjacent ecosystem | Moderate | Large |
| Directly identifiable primary owner | No | No |
| Ease of minimum viable prototype | High | Moderate |
| Semantic difficulty | Moderate | High |
| Main correctness risk | False equivalence between two executions | False staleness or false persistence |
| Most useful first output | Observation-fidelity delta and risk evidence | Freshness graph plus selective rerun plan |
| Best positioning | Observation-fidelity guard, not another test runner or hook | Claim-level incremental truth maintenance, not another build system or knowledge graph |

The two candidates also differ in what they would need to prove. Candidate A needs adversarial command traces that demonstrate it can recover hidden failures. Candidate B needs a corpus of claims, inputs, and deliberate changes that demonstrate selective invalidation without unnecessary recomputation. Both should publish a negative-result policy: what they do not verify, which nondeterministic executions they refuse to compare, and which dependencies they cannot model.

## 7. The defensible novel claim is a primary function, not a claim of universal novelty

**The most defensible statement is: there is no verified public tool whose primary contract is to compare an AI coding agent’s observed shell result with a clean-channel re-execution and report the exact fidelity delta, including exit-code laundering and hidden terminal output.** This statement concerns a public, primary, observed contract. It does not say that no tool captures shell output, blocks commands, compresses terminal text, or audits agent behavior. It does not claim that the component is impossible to build, that future projects will not overlap, or that every niche in the wider space is vacant.

A secondary but still defensible claim is: **no verified public tool combines local verification claims, explicit content-digested input dependencies, selective stale-claim propagation, and claim-level re-verification as its primary function.** Bazel and Nix implement incremental invalidation; GUAC represents software metadata in a graph; CocoIndex and similar systems materialize incremental transformations; ageval preserves and reproduces agent traces. The gap is the epistemic object—“this claim is valid because these specific evidence inputs had these specific digests”—and the freshness operation built around it.

The strongest honest caveat is that **absolute global novelty cannot be proven**. Public-web evidence is incomplete. A project may be private, recently renamed, pre-release, described only in conversation, implemented inside an enterprise harness, or using terminology not captured by the searches. Even a cleanly stated contract may later be found to overlap with an obscure tool. The appropriate research standard is therefore not “nothing like this exists anywhere,” but “no directly identified incumbent owns this primary contract, and these are the nearest neighbors.”

## 8. The recommended scope is one claim contract with two clearly denied boundaries

**Build candidate A first, but specify it as an observation-fidelity guard rather than a verification platform.** Its primary output should be a structured comparison between what the agent observed and what a clean observation channel produced. It should explicitly not verify whether the command was semantically correct, whether the test suite was adequate, whether the repository policy permitted execution, or whether a durable receipt was signed. Those functions belong to verifiers, test frameworks, sandbox policy, and audit formats.

A minimum viable specification should record the following for each observed command:

| Field | Purpose |
|---|---|
| Original command text | Preserves the exact string proposed by the agent |
| Parsed transformation graph | Identifies pipes, redirects, command separators, environment changes, and background execution |
| Raw standard output | Records the complete output of the clean channel |
| Raw standard error | Separates error output from standard output |
| Raw exit status | Becomes the canonical execution outcome |
| Observed text | Records the exact text delivered to the agent |
| Observation channel | Identifies the harness, hook, proxy, or terminal boundary |
| Re-execution policy | States whether and why a clean rerun was permitted |
| Delta verdict | Reports added, removed, hidden, or transformed information |
| Evidence artifacts | Links to complete output, command transcript, and rerun result |

The system should issue one of four delta classes: observation-equivalent; lossy but not conclusion-changing; lossy and conclusion-changing; or indeterminate because the clean rerun was not equivalent. The third class is the highest-value security and correctness signal. The fourth is not a failure: it is an honest admission that observation fidelity cannot be established across two non-equivalent executions.

It should also implement a strict allow-or-refuse policy for re-execution. Deterministic commands over immutable local inputs may be rerun safely. Commands with network access, destructive side effects, secrets, time dependence, or external concurrency should be marked unverifiable rather than executed again. Otherwise, the integrity wrapper becomes an attack surface larger than the agent it supervises.

**Candidate B should be scoped as a local truth graph, not a new knowledge graph or CI system.** Each claim should have an explicit predicate, evidence reference, validity interval, input manifest, and dependent claims. It should distinguish at least five states: verified, inconclusive, conditionally verified, stale, and unsupported. “Conditionally verified” is essential: a claim may be valid only for a declared toolchain, environment, or dependency set. “Stale” must remain a separate state from “false”; a stale claim is not yet disproved, but may no longer be relied upon.

The graph should support three principal operations:

1. **Bind** a new verified claim to the digests and execution context that produced it.
2. **Propagate** staleness from a changed input to its direct claims and then to their transitive dependents.
3. **Reconcile** by rerunning only the affected claims and producing a freshness explanation.

This scope excludes general semantic search, model memory, document ingestion, and repository-wide knowledge management. Including those functions would turn candidate B into a generic graph platform and weaken the novelty claim.

## 9. The competitive boundary must be stated in primary functions, not tool categories

The safest way to position either project is to name the nearest incumbent and state exactly what the new tool will not do. This prevents the earlier error of treating broad absence as a design vacuum.

| New function | Closest existing tool | Exact functional difference | Do not claim |
|---|---|---|---|
| Observation-fidelity delta | honestly | honestly checks assertions and selected command forms; the new tool preserves raw output, creates a clean channel, and reports a delta | “No one blocks bad commands” |
| Clean-channel re-execution | RTK | RTK deliberately compresses output; the new tool preserves and compares the raw result | “No one intercepts shell output” |
| Over-compression detection | TACO | TACO optimizes agent context; the new tool proves observation equivalence | “No one compresses terminal output” |
| Claim freshness graph | Bazel | Bazel invalidates build actions; the new tool invalidates verification claims | “No one does incremental builds” |
| Input-digested evidence | Nix | Nix derives outputs from content-addressed derivations; the new tool models evidence dependencies | “No one uses content hashes” |
| Metadata graph | GUAC | GUAC aggregates supply-chain metadata; the new tool tracks local claim validity | “No one builds graphs” |
| Reproducible traces | ageval | ageval reproduces agent tasks; the new tool determines which old claims remain valid | “No one records traces” |
| Audit-log format | PALA-1 | PALA-1 standardizes portable logs; the new tool decides observation fidelity or claim freshness | “No one issues receipts” |

The table also shows why a claim of “zero-dependency wrapper” should be narrowed. A useful implementation will still need a shell parser, a terminal emulator or ANSI decoder, a diff engine, and secure execution isolation. “Zero-dependency” should therefore describe its runtime integration footprint—no agent SDK, no server, no model call—not its internal libraries. A misleading dependency claim would weaken an otherwise strong novelty argument.

## 10. Evidence quality is mixed, so conclusions must remain conditional

This review found a meaningful adjacent ecosystem but not the two proposed primary functions. Public material on honestly, RTK, and TACO is sufficient to establish their roles as command assertion checking, terminal transformation, and adaptive output compression respectively. Foundational supply-chain, build, and audit mechanisms are also well established. The newer supplied repositories, however, were not confirmed from canonical primary pages in this research pass.

**The negative conclusion is evidence-supported but intentionally limited.** It is based on direct searches for the requested failure modes and for tools that preserve both observed and raw shell output, re-execute commands in a clean channel, bind claims to content-digested inputs, and selectively invalidate verification claims. No directly returned public tool was found to own either complete function. The result should be treated as a current public-web null result, not a global nonexistence proof.

The following claims therefore remain **unverified** and should not be used as the sole basis for a novelty declaration:

- Repository URLs, license, implementation language, and maturity for alibi, Reverify, CodeVetter, anti-fake-complete, PALA-1, and agent-receipts.
- The existence, field layout, and interoperability of PALA-1 test vectors and authenticiq verifier schemas.
- The exact semantic behavior of the supplied tools beyond the supplied descriptions.
- Quantitative comparisons of adoption, performance, false-positive rates, or detection coverage.
- Whether an unindexed private, enterprise, or renamed project already implements candidate A or candidate B.

A pre-announcement verification should inspect the actual repositories, release artifacts, documentation, and tests for each supplied project; test whether honestly preserves raw output and reruns commands; confirm the existence and syntax of PALA-1 and agent-receipts schemas; and search code-hosting platforms and package registries for additional near-neighbors. Until that work is complete, the strongest sustainable claim is that the two candidate slices remain **narrowly and defensibly unowned in their proposed primary forms**, not that the surrounding space is empty.

## 11. The final answer: build observation fidelity first, then claim freshness

**There is no remaining genuinely unoccupied broad primary function in agent evidence infrastructure.** Audit logs, receipts, provenance, hooks, sandboxing, verification, evidence-level grading, incremental builds, supply-chain metadata, and output compression are all occupied to some degree. The viable opening is a **narrower claim contract** that existing tools touch but do not own.

**Candidate A is less occupied.** honestly is the strongest near neighbor, but its function is assertion and command-form checking, not observation-fidelity delta reporting. RTK and TACO deliberately transform the output rather than proving that the transformation preserved the conclusion. A tool that records exactly what the agent saw, reruns the command in a clean channel, and proves the delta would not be a test runner, a hook, a receipt format, or a sandbox.

**Candidate B is more conceptually original but less clearly unoccupied.** It would be valuable as a local truth graph for verification claims, but it overlaps Bazel’s action graph, Nix’s content-addressed derivations, GUAC’s software metadata graph, and CocoIndex-style incremental materialization. Its defensible novelty would be claim-level freshness semantics, not incremental computation in general.

**The final narrow statement is: there is no verified public tool whose primary contract is observation-channel integrity through clean-channel re-execution and exact delta reporting; and there is no verified public tool whose primary contract is a local incremental truth graph that invalidates and selectively re-verifies agent evidence claims by content-digested inputs.** Both statements are conditional on the limits of public search and should be rechecked against primary repositories before product launch or publication.

## Data sources

[1] https://news.qq.com/rain/a/20240928A0AA2E00
> “更大的转变是从设计仅仅‘被信任’的系统，转向设计其具有实质影响的行为可被审查和证明的系统。”

[2] https://finance.sina.com.cn/stock/t/2026-06-03/doc-iniaamhz1163640.shtml
> “现有的评测 为何‘集体失明’？……现有基准存在两大致命缺陷：缺陷一：只评估文本输出，完全忽视物理后果。”

[3] https://new.qq.com/rain/a/20251023A0ATAQ00
> “EvidenceBook为参与方提供各自签名的交易历史记录……验证可以离线进行，且免费。”

[4] https://www.163.com/dy/article/LB7IACIR05561FZL_pdya11y.html
> “工具输出可以提议一个动作，但永远不能授权一个动作。”

[5] https://www.163.com/dy/article/LB58R2AO05561FZE_pdya11y.html
> “这类命令会被拒绝，并给出一行修正方案。其余命令不动：pytest | tail 保留了摘要行，所以放行。”

[6] https://www.163.com/dy/article/LB58R2AO05561FZE_pdya11y.html
> “在回复送达之前，honestly 读取这一轮的对话记录，寻找‘测试通过’‘修好了’‘构建成功’‘已推送’这类句子。”

[7] https://news.qq.com/rain/a/20260512A07WBD00?id=20260512A07WBD00
> “RTK 的核心处理方式主要包括四类：智能过滤……分组聚合……截断机制……去重。”

[8] https://news.qq.com/rain/a/20260512A07WBD00?id=20260512A07WBD00
> “它提供了 Auto-Rewrite Hook，可以在支持 hook 的 Agent 中自动拦截 Bash 命令，并把普通命令改写成 RTK 命令。”

[9] https://news.qq.com/rain/a/20260507A02SIU00
> “TACO 会在真实交互轨迹中观察哪些规则有效、哪些规则可能压缩过度。”

[10] https://news.qq.com/rain/a/20260507A02SIU00
> “所谓的‘规则’并非模糊的自然语言提示词，而是由触发条件、保留模式和剔除模式组成的函数。”

[11] https://baike.baidu.com/item/in-toto/67894051
> “in-toto是一个软件供应链安全框架，旨在确保软件从开发到分发的整个生命周期中每个步骤的完整性与可验证性。”

[12] https://baike.baidu.com/item/TACO/67779476
> “规则在线精炼与修复：根据任务执行的实时反馈迭代调整规则边界，修复过度压缩或遗漏关键信号的问题。”

[13] https://news.qq.com/rain/a/20251122A04JO100
> “给 Claude 这么大的访问权限可能会引入风险，特别是在提示词注入的情况下。”

[14] https://mirrors.tuna.tsinghua.edu.cn/tuna/tunight/2021-05-29-nix/slides.pdf
> “target : prerequisites recipe … prerequisites are referenced in the recipe, thus should be considered part of the recipe.”

[15] https://www.163.com/dy/article/HK7UM0H80511BLFD.html
> “GUAC 是一个免费的工具，可以将许多不同来源的软件安全元数据结合起来。”

[16] https://www.163.com/dy/article/KS8GM2AQ0519EA27.html
> “源变了或者代码（F）变了，引擎自动算出 delta 重跑。”

[17] https://baike.baidu.com/item/MyContext/68607959
> “MyContext 以本地化方式运行于用户设备，可将……多源数据，自动沉淀为一份持续更新的工作档案。”

[18] https://news.qq.com/rain/a/20260816A04CW200
> “组织如今越来越需要建立信任的对象不仅包括源代码，还包括 AI 生成的工件、自动化工作流、基础设施变更和自主软件交付流程。”

[19] https://baike.baidu.com/item/CodeGraph/67845171
> “变更影响测试追踪：codegraph affected 命令可追踪变更文件的传递依赖，精准定位受影响的测试文件。”

[20] https://news.qq.com/rain/a/20260921A09JSI00
> “针对 Agent 常见问题，平台内置异常规则，覆盖模型侧和工具侧。输出截断、工具超时、参数异常等问题可以自动标记。”

[21] https://www.163.com/dy/article/LB9HNT2E05561FZE_pdya11y.html
> “相关文件和提示词都放在仓库的 demo/ 目录里，可以自己复现。”

[22] https://news.qq.com/rain/a/20260722A04Z4M00
> “Completeness 强调的则是：我们对风险的考虑是否足够完整。”

[23] https://news.qq.com/rain/a/20260820A0BY2Q00
> “你以为无关紧要的地方，浮点数精度。”

[24] https://software.nju.edu.cn/English/News/Selected/20260901/i414626.html
> “Such ‘stale function references’ are not merely a readability issue—they can mislead maintainers, hinder code comprehension.”

[25] https://www.163.com/dy/article/LBG1R58705561FZG_pdya11y.html
> “每个字段都能链回源图像的坐标、置信度和复核状态。”

[26] https://new.qq.com/rain/a/20261003A000EU00
> “Agent 的状态也不能只理解成‘它记住了多少聊天记录’。”

[27] https://www.163.com/dy/article/LBFKUBDN05561FZW_pdya11y.html
> “一个粗糙的检查器可能会去找评估事件，比对候选对象，看到 independent-reviewer，然后返回 PASS。”

[28] https://news.qq.com/rain/a/20260611A02J7V00
> “当 Agent 能够疯狂操作 Tool 时，仅看最终任务成败已经不够了。”

[29] https://news.qq.com/rain/a/20260127A01SPM00
> “不是简单的一次性运行，而是持续迭代直到完成任务。”

[30] https://news.qq.com/rain/a/20260407A04FT100
> “对代码文件通过 tree-sitter 做本地 AST 解析直接提取结构信息……全程在本地完成，不调用 LLM。”
