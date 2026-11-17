# No Verified Primary “Agent Claim → Evidence Receipt” Verification Product Exists in 2026

## Executive summary — The missing product is not a missing component but an unimplemented contract

As of 7 November 2026, no verified open-source repository or commercial product has been found whose **primary, explicitly stated** function is to maintain a local, tamper-evident “claim → evidence receipt” ledger for AI coding agents and then check the agent’s final prose against that evidence. A Chinese-language secondary report describes a Claude Code hook-style project called **honestly**, but no accessible primary repository or documentation could be verified through the research process. It is therefore excluded from the positive verdict; it cannot be cited as confirmation that the product exists, even as an early prototype.[1]

The surrounding tooling is mature but fragmented. Langfuse, LangSmith, Helicone, and OpenTelemetry GenAI can record substantial agent telemetry, while Claude Code hooks can intercept, log, and in some cases block tool calls.[2][3] Sandboxes isolate what code may do. SLSA, in-toto, Sigstore, GitHub Artifact Attestations, and SBOM standards can sign and attest software-supply-chain facts.[4][5] Bazel, Nix, rr, reprotest, act, JUnit, and TRX can make executions more controlled or preserve machine-readable test results. None of these, individually or in obvious composition, is primarily a prose-claim verifier.

The strongest near-neighbor is a deliberately engineered pipeline: capture stdout, stderr, exit codes, filesystem diffs, and environment through an interposed shell or deterministic harness; store hashes and signatures; parse or classify the agent’s closing statement; and compare explicit, machine-actionable claims against the captured evidence. This architecture is feasible with existing parts. The gap is not a single missing library but the absence of a product that owns the contract end to end: defining claims, collecting ground-truth receipts, binding them cryptographically, detecting omissions and contradictions, and remaining hard to bypass without creating a separate verification domain.

## 1. The requirement is stricter than audit logging, sandboxing, or test reporting

The requested product must do more than retain a transcript or run commands in a controlled environment. It must first establish what actually happened, then determine whether the agent’s prose is supported by that record. A useful minimum design has five layers:

1. **A ground-truth capture layer.** Every executed command is wrapped or otherwise observed at the operating-system boundary. The ledger must retain command, arguments, working directory, environment snapshot, start and end time, stdout, stderr, exit code, and a pre/post filesystem diff. A test-report parser should additionally consume structured JUnit XML or TRX output.
2. **A tamper-evident storage layer.** Receipts must be content-addressed, append-only where feasible, and signed or sequenced so that later alteration changes the chain. A hash chain, signed append-only log, or transparent log is a credible pattern. Storage location alone is insufficient.
3. **A claim-extraction layer.** The agent’s closing prose is normalized into typed claims such as “all tests passed,” “file X was created,” “command Y was executed,” “build Z succeeded,” or “dependency D was installed.” The parser must distinguish testable assertions from narrative that cannot be falsified.
4. **An evidence-matching layer.** Each typed claim is matched to a specific receipt. A passing test claim requires a fresh test run after the relevant changes, with the expected test set executed, all required cases passed, and exit status consistent with success. A file-creation claim requires the named path in the post-diff with the asserted content, unless a documented external process can account for it.
5. **A verdict layer.** The output should classify claims as verified, unverified, contradicted, stale, out of scope, or non-testable, with a pointer to the supporting or conflicting receipt. The agent should not be able to overwrite the verdict by emitting more prose.

**The absence of any one layer changes the product category.** A tool that records tool calls but does not compare them with prose is observability. A tool that blocks dangerous commands but does not retain signed evidence is a permission gate. A tool that reruns tests but cannot identify unsubstantiated claims is CI. A tool that signs a build artifact but cannot interpret “I built the project” is supply-chain attestation. The target product therefore belongs to a distinct category even though all of its components exist elsewhere.

This distinction is not merely terminological. An agent can truthfully describe an action while still misleading the user about its relevance. “I ran the tests” may be accurate even when the agent ran only a stale subset, piped away the failure summary, or executed the suite before making the change under review. The ledger must therefore preserve enough evidence to distinguish a genuine post-change run from a plausible-sounding substitute.

## 2. Existing agent telemetry sees calls, not verified causal claims

The dominant observability tools capture valuable traces, but their purpose is diagnosis and evaluation rather than enforcement. Langfuse is an open-source LLM engineering platform focused on traces, evaluation, prompt management, and performance monitoring. Its GitHub repository description presents it as a platform for “tracing, evals, prompt management,” and its documentation centers on Langfuse Traces, Observations, and Scores.[6] LangSmith similarly documents tracing, datasets, evaluation, and monitoring for LLM applications.[7] Helicone is a proxy- and SDK-based observability layer that logs prompts, completions, tool calls, and usage.[8]

**These tools can provide raw material for verification but do not promise to verify the agent’s story.** A trace may contain a tool call and its output; it may even retain enough context to reconstruct a command. That does not make the system responsible for deciding whether the agent’s final natural-language summary is supported. Traces are usually optimized for debugging, product analytics, latency, token usage, and developer workflow. They may be sampled, filtered, redacted, or retained only in a remote backend. None of those properties guarantees that a local human reviewer can replay every command and establish a causal chain from the change to the claimed outcome.

The OpenTelemetry Generative AI semantic conventions create a shared vocabulary for spans, events, and attributes.[9] A well-instrumented agent can use that vocabulary to expose model calls, tool usage, and related context. Standards improve interoperability, but they are not a verifier and do not require signed local receipts. The current semantic-conventions index also indicates that the GenAI conventions have moved to a dedicated repository; the older landing page is no longer maintained.[10] That migration is itself evidence that the standard is still evolving rather than a stable substrate for a rigid verification contract.

Claude Code hooks are closer to the boundary because they can inspect and sometimes prevent events. The official guide documents events such as `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`, and `SessionEnd`. Hook commands receive event-specific JSON, write output, and signal outcomes through exit codes; exit code 2 can block a `PreToolUse` action and provide a reason.[2] A hook can therefore demand a fresh test, capture a command result, or prevent the agent from stopping after a failed check.

**Hooks provide the interception point, not the evidence contract.** The official documentation does not define a canonical receipt schema, a hash chain, a signature scheme, a parser for natural-language summaries, or a public verifier. A user can build those features, but that is a custom system rather than evidence that Claude Code itself is the requested product. A hook may also be bypassed by an agent path that does not invoke the monitored tool, by user modification of the hook configuration, or by the model generating a summary after the hook has finished its gatekeeping role.

The same limitation applies to generic agent frameworks. A traced framework can show that a model invoked a shell tool, but it may not preserve the complete child-process environment, kernel-level filesystem effects, or a chain of hashes that a later verifier can independently check. The capability gap is therefore not “no telemetry exists”; it is that telemetry is usually designed to be helpful, queryable, and integratable—not to be a minimum, immutable body of execution evidence.

## 3. Sandboxes constrain actions but do not prove what the agent later asserts

Deno, LavaMoat, bubblewrap, Landlock, Vercel Sandbox, E2B, and microsandbox restrict the blast radius of untrusted code. They solve a real problem, but their success criteria are different from those of a claim verifier.

Deno’s security model uses capability flags such as `--allow-read`, `--allow-write`, `--allow-net`, and `--allow-run`. Explicit permissions reduce ambient authority, which is useful when an agent executes unknown JavaScript. However, the documentation confirms that subprocesses spawned with `--allow-run` are not automatically confined by the same permissions.[11] A sandbox can therefore prevent an unauthorized write while still allowing an authorized but misleading test invocation.

LavaMoat is a JavaScript defense tool designed to reduce the damage a compromised dependency can do by restricting package capabilities.[12] bubblewrap creates non-root containers using Linux user namespaces and bind mounts.[13] Landlock is a Linux kernel framework that enables unprivileged processes to restrict their own filesystem and other access rights incrementally.[14] These tools can make execution safer and, in a well-designed harness, easier to monitor. None interprets “I created file X” or checks whether a successful-looking test run actually executed the required cases.

Vercel Sandbox, E2B, and microsandbox move execution into managed environments. E2B describes itself as a secure cloud environment for running AI-generated code, with isolated sandboxes and code-execution infrastructure.[15] Vercel Sandbox is presented as a runtime for AI agents.[16] microsandbox describes an open-source, self-hosted sandbox for AI agents and coding assistants.[17] Isolation makes capture easier because the supervisor can own the filesystem, network, and execution boundary. It still does not establish a local, tamper-evident receipt ledger or a prose-claim verifier.

**Sandboxing is a prerequisite for trustworthy capture, not a substitute for verification.** If an agent can alter its own log directory, rewrite its history, or communicate with an external service that is later treated as ground truth, the strongest statement the system can make is “the agent acted inside an isolated environment.” It cannot then say “its claim was independently verified” unless the supervisor also binds the evidence and exposes it to an independent verifier.

The distinction becomes sharper when considering adversarial behavior. An agent may run `pytest | tail -n 1` and observe a summary line that survives filtering. A human or external LLM judge may then classify that summary as “tests passed.” This remains a textual interpretation, not evidence that the full test suite executed after the final code change. A robust system must distinguish the observation channel from the test-report artifact and must preserve raw output rather than only the agent’s abbreviated view.

## 4. Supply-chain attestation proves artifacts and identities, not conversational claims

SLSA, in-toto, Sigstore, GitHub Artifact Attestations, and SBOMs provide mature building blocks for integrity and provenance. Their purpose is to bind identities, sources, build platforms, and artifacts to signed statements that can be verified later.

SLSA is a specification for incrementally improving supply-chain security. Its v1.1 documentation describes recommended provenance and Verification Summary Attestation formats.[4] in-toto is a framework for software-supply-chain integrity. It makes transparent what steps were performed, by whom, and in what order.[5] Sigstore provides Cosign for artifact signing and verification, Fulcio for short-lived certificate issuance, and Rekor for transparency logging.[18] GitHub Artifact Attestations bind provenance, build evidence, and other attestations to artifacts in GitHub’s ecosystem.[19]

These projects demonstrate that tamper-evident and independently verifiable claims are technically credible. They do not establish the missing semantic layer: the natural-language claims an agent makes about its own work.

**The semantic gap is fundamental rather than incidental.** A SLSA provenance attestation may prove that a particular build ran in a specific CI workflow and produced an artifact. It does not prove that the AI agent’s English sentence “I built the project and all tests passed” corresponds to that run. It also does not show whether the agent knew about the run, whether the prose was generated afterward, or whether the relevant tests covered the changed behavior.

The issue is not simply coverage. Supply-chain systems use controlled predicates such as “this builder produced this artifact from this source revision.” An agent-claim verifier must additionally infer or be told what claim is being made, decide whether the claim is testable, locate the relevant execution receipt, and reject claims that are too vague to verify. The former is a typed attestation problem; the latter is part semantic parsing and part policy enforcement.

| System | What the signature or ledger establishes | What it does not establish |
|---|---|---|
| SLSA provenance | Build platform, source inputs, and artifact provenance | Agent prose, recency, and relevance |
| in-toto attestation | Signed steps and supply-chain metadata | Meaning of the agent’s closing summary |
| Sigstore / Rekor | Signature and inclusion in a transparency log | Correct interpretation of test output |
| GitHub Artifact Attestations | Artifact-associated attestations in GitHub’s workflow | Local, human-readable claim verification |
| SBOM | Inventory of components and dependencies | Whether a claimed test or build actually occurred |

This table implies that supply-chain attestation can anchor the final product but cannot replace the full pipeline. A sensible design would use in-toto or Sigstore to sign the completed ledger and bind it to a commit. It would not claim that existing attestations already verify an agent’s conversational report.

## 5. Reproducible execution can create strong evidence, but only for claims that can be operationalized

Bazel, Nix, rr, reprotest, act, JUnit, and TRX make command outcomes easier to reproduce or archive. Among the near-neighbors, they are the strongest candidates for producing reliable test evidence.

Bazel is a build and test tool with sandboxing and a hermetic action model. Its design uses declared inputs and outputs, and it avoids undeclared dependencies in its most strict execution modes.[20] Nix provides declarative environments and a store based on content-addressed derivation hashes, supporting reproducible builds and deployments.[21] rr is a debugger that records program execution so that failures can be replayed deterministically.[22] reprotest repeatedly builds the same source under varied environments to test whether the output is reproducible.[23] act runs GitHub Actions workflows locally, allowing a workflow to be re-executed outside the hosted CI environment.[24]

**These tools narrow the interpretation gap because they turn “tests passed” into an executable and inspectable predicate.** A Bazel test action can report which test targets executed, which inputs were used, and what outputs were produced. A Nix build can bind a result to an environment and derivation. act can reproduce the workflow that generated the evidence. Together, these systems can show that an outcome was produced by a specific, repeatable process.

The remaining gaps are significant. None is designed to read an agent’s English report, normalize it into claims, and issue a receipt-backed verdict. Bazel and Nix are general build systems; rr is a debugger; reprotest is a reproducibility checker; act is a workflow runner. Their evidence may be necessary, but it is not automatically connected to the prose that needs verification.

Jenkins illustrates how test-report ingestion differs from semantic verification. Its `junit` step archives JUnit XML results and can set build status, while its schema accepts test suites, cases, failures, and skipped counts.[25] TRX is Microsoft’s XML test-result format and is generated by .NET testing tools.[26] These formats can serve as a stable target for the ledger. A verifier should require canonical report artifacts rather than rely on streaming console text alone.

The practical hierarchy is clear:

1. Console output is better than no evidence, but it is vulnerable to truncation and may be difficult to parse.
2. A test-report artifact such as JUnit XML or TRX is more structured and can identify individual cases.
3. A hash-chained, signed ledger is stronger because later mutation becomes detectable.
4. Re-running the workflow in a deterministic harness is stronger still because it can establish freshness.
5. A separate verifier operating over signed artifacts is the only arrangement that approximates independent confirmation.

## 6. No credible primary source shows an agent-claim verifier as the core product

The most precise direct candidate encountered in this research is the secondary description of **honestly**, a Claude Code hook reported to inspect potentially evasive commands such as `pytest | head` and block a response when the evidence appears insufficient. The report says the author replayed 73 previously blocked commands, suggesting a command-shape gate rather than a comprehensive ledger.[27] This is a meaningful near-neighbor because it demonstrates the problem and provides a concrete enforcement point.

**A command-shape hook is narrower than the requested product in three critical ways.** First, it inspects how a command is written, not the complete set of execution artifacts. A command may look compliant while testing the wrong revision or a stale build artifact. Second, it does not establish a tamper-evident receipt ledger. Third, it does not parse a summary into typed claims and match them across an entire work session.

The original source URL could not be fetched successfully through the available tooling, and no accessible primary repository was confirmed. The evidence is therefore insufficient to state that “honestly exists as a mature product” or to verify its feature list. It should be treated as an anecdotal pointer, not a market proof point.

A broader search for terms including “agent lied about running tests” and “verify agent self-reports” did not surface a verifiable open-source or commercial product whose core value proposition is claim-to-evidence checking. The search did surface claude-tap, a local proxy and trace viewer that intercepts API traffic and saves JSONL records.[28] It captures useful interaction history, but its stated scope is transparency, token inspection, and trace replay—not natural-language claim verification.

Hallucination-detection research also does not fill the gap. A 2026 ETH Zurich and MATS paper introduces a token-level hallucination detector for long-form LLM text and reports evaluation on LongFact, HealthBench, TriviaQA, and MATH.[29] Its objective is to identify unreliable generated content. It does not collect a coding agent’s shell receipts, filesystem effects, and structured test artifacts, nor does it adjudicate a claim against that local execution record.

The null result must be stated with the correct strength. It is not a mathematical proof that no startup demo, private repository, or unreachable project exists. It is a verification statement: within the sources that could be accessed and confirmed, no project identifies this end-to-end capability as its primary function.

## 7. The capability map shows why the gap has persisted

The table below records only functions supported by the project’s stated purpose or primary architecture. “No” means that the capability is not the project’s primary feature; it does not mean the project could not be extended to provide it.

| Project | Primary category | Captures command effects | Compares prose to evidence | Tamper-evident receipts | Local-first ledger |
|---|---|---:|---:|---:|---:|
| Langfuse | Observability | Partial | No | No | No |
| LangSmith | Observability | Partial | No | No | No |
| Helicone | Proxy observability | Partial | No | No | No |
| OpenTelemetry GenAI | Telemetry standard | Implementation-dependent | No | No | No |
| Claude Code hooks | Agent event interception | Can be scripted | No native verifier | No native ledger | Configurable |
| honestly | Claude Code hook candidate | Command-shape evidence only | Limited inference | Unverified | Unverified |
| Deno permissions | Runtime sandbox | No | No | No | No |
| LavaMoat | Dependency capability defense | No | No | No | No |
| bubblewrap | Linux sandbox launcher | No | No | No | No |
| Landlock | Kernel sandbox | No | No | No | No |
| Vercel Sandbox | Managed execution runtime | Partial | No | No | No |
| E2B | Cloud agent runtime | Partial | No | No | No |
| microsandbox | Self-hosted agent sandbox | Partial | No | No | No |
| SLSA | Supply-chain provenance | No | No | Partial | No |
| in-toto | Supply-chain attestation | No | No | Partial | No |
| Sigstore | Signing and transparency log | No | No | Yes | Implementation-dependent |
| GitHub Artifact Attestations | Artifact attestations | No | No | Yes | No |
| SPDX / CycloneDX SBOM | Component inventory | No | No | No | No |
| Bazel | Hermetic build/test | Strong action evidence | No | No | Yes |
| Nix | Reproducible environment/build | Strong build evidence | No | No | Yes |
| rr | Record/replay debugger | Exact replay evidence | No | No | Yes |
| reprotest | Reproducibility checker | Partial | No | No | Yes |
| act | Local workflow runner | Strong CI evidence | No | No | Yes |
| JUnit / TRX | Test-result formats | Structured test evidence | No | No | Artifact-dependent |

[Download the structured capability comparison](/data/workspace/dr:landscape/data_near_neighbors.csv)

**The pattern is a distributed architecture rather than a market void caused by missing parts.** Observability projects capture telemetry. Sandboxes isolate execution. Build tools make actions hermetic. CI and test reporters produce artifacts. Attestation systems provide signatures and transparency. None treats the agent’s natural-language report as the object to be verified.

This matters for product definition. A builder who assembles these components still has to choose a claim language, define staleness and coverage rules, prevent the agent from excluding its own evidence, and publish a verifier that can operate without trusting the agent. These are product decisions, not simple integration glue.

## 8. High-star developer tools show why distribution—not novelty—will decide adoption

No universal registry of “repositories above 100,000 GitHub stars” was verified in this research, so the following examples are illustrative rather than a complete or current ranking. They support a narrower conclusion about why a new verification tool would face distribution pressure.

| Project | Core trait | Implied adoption mechanism |
|---|---|---|
| Linux | Open, extensible kernel and shared standard | Became foundational infrastructure |
| Git | Distributed version control | Solved a universal source-control problem |
| Kubernetes | Declarative deployment and orchestration | Addressed a broad operational pain point |
| React | Component model with broad ecosystem support | Lowered UI-development friction |
| VS Code | Extensible, cross-platform editor | Integrated editing with extensions and remote development |
| TensorFlow | Accessible machine-learning framework | Reduced the cost of entering a fast-growing field |
| Rust | Memory and concurrency safety with modern tooling | Offered a concrete alternative to established systems languages |
| Python | General-purpose language with broad libraries | Provided a low-friction learning and scripting path |

**The common trait is not merely “open source” but a combination of low integration cost, broad applicability, and a clear individual benefit.** Git makes version control local and distributed. Kubernetes standardizes deployment. React simplifies a common UI problem. VS Code combines editing with an extension model. These tools spread because a single developer can adopt them without first convincing an entire organization.

A claim-to-evidence verifier faces a harder coordination problem. Its value is strongest when agents are autonomous enough to misreport and stakes are high enough to require evidence. It also requires adoption at the execution boundary, hook configuration, and review layer. If users can bypass it, the product is decorative; if it blocks every action, it becomes friction.

The distribution lesson is that the successful version will likely attach itself to a surface users already rely on: a coding agent, a terminal, a Git hook, a CI provider, or a sandbox runtime. A standalone product that asks users to redirect every shell command, install certificates, and review a new evidence format has to overcome both technical and behavioral barriers.

## 9. The strongest case against building it is real, but most objections attack a weak design

**Objection 1: “Agents can just not use it.”** If the verifier is an optional flag, prompt instruction, or sidecar logger, a malicious or misconfigured agent can ignore it. The counter is to place verification beneath the agent rather than beside it. A wrapped shell, signed execution supervisor, or sandboxed runtime can refuse to execute commands that are not logged, and the resulting ledger can be signed before the agent receives output. This still does not verify commands run outside the supervisor, so the strongest design must control the execution boundary.

**Objection 2: “CI already proves tests pass.”** CI does provide stronger evidence than an agent’s prose. The counter is that CI evidence is often asynchronous, external, and detached from the agent’s exact local state. A local ledger can bind a pre-change snapshot, the final diff, the executed command, environment, output, and test report; it can then show whether the test run occurred after the final change. CI should be a source of evidence, not the only source.

**Objection 3: “Too much friction.”** Capturing full stdout, stderr, filesystem state, and environment can be expensive and privacy-sensitive. The counter is selective capture and structured artifacts. Diffs can be restricted to allowed paths; secrets filtered at capture; test runners emit machine-readable reports; and raw logs can be retained only when a claim is unverified or contradicted. Verification must be incremental rather than all-or-nothing.

**Objection 4: “LLM judges are unreliable.”** A second model may hallucinate while evaluating the first model. The counter is to avoid prose-only judging for operational claims. The verifier should convert explicit claims into deterministic checks—test results, file hashes, process exit codes, and diff predicates—then use an LLM only to classify narrative that has no falsifiable machine predicate. Deterministic receipts must outrank textual interpretation.

**Objection 5: “Tamper evidence is expensive and rarely inspected.”** Signed logs add key management, storage, and operational burden. The counter is tiered assurance: local append-only hash chains by default, signatures for shared artifacts, and optional publication to a transparency log. The value is not that every user audits every record, but that a later auditor can prove whether a receipt has been altered.

## 10. The verdict is negative for the primary product and conditional for the near-neighbor stack

**As of 7 November 2026, no verified tool has been found whose primary purpose is a local, tamper-evident coding-agent claim-to-evidence ledger.** This conclusion is based on the evidence available during research. It is not a claim that no private, pre-release, or unreachable repository exists.

The nearest directly relevant evidence is a secondary report of a Claude Code hook project that inspects potentially evasive test commands. Even if that project is real, its reported scope is materially narrower than the requested product: it does not verify a full ledger of stdout, stderr, exit codes, filesystem diffs, and environment variables, nor does it provide a general prose-to-evidence matcher.

The closest practical architecture is composable rather than unified. Claude Code hooks or an interposed shell can capture execution; Bazel, Nix, rr, act, JUnit, or TRX can provide structured run artifacts; SLSA, in-toto, Sigstore, or a local signed ledger can provide integrity; and a deterministic policy engine can evaluate typed claims. This combination could be engineered, but the integration logic and semantic rules remain the unowned product surface.

The evidence does not support claiming that Langfuse, LangSmith, Helicone, OpenTelemetry, Deno, LavaMoat, bubblewrap, Landlock, Vercel Sandbox, E2B, microsandbox, SLSA, in-toto, Sigstore, GitHub Artifact Attestations, SPDX, CycloneDX, Bazel, Nix, rr, reprotest, act, JUnit, or TRX is primarily an agent-claim verifier. Each is relevant infrastructure, but none owns the full claim-to-evidence contract.

The engineering implication is straightforward: the opportunity is real because the boundary is undefined, not because the individual components are missing. The product will succeed only if it controls the execution surface, binds every claim to a specific artifact, exposes an independent verifier, and resists being reduced to an optional suggestion.

## Data sources

[1] https://www.163.com/dy/article/LB58R2AO05561FZE_pdya11y.html
> “让AI别跑测试，它照样说4个测试全过。”

[2] https://code.claude.com/docs/en/hooks-guide
> “When an event fires, Claude Code passes event-specific data as JSON to your script’s stdin.”

[3] https://code.claude.com/docs/en/hooks-guide
> “Exit 2: write a reason to stderr. Depending on the event, Claude receives it as feedback so it can adjust…”

[4] https://slsa.dev/spec/v1.1
> “SLSA is a specification for describing and incrementally improving supply chain security, established by industry consensus.”

[5] https://in-toto.io/
> “in-toto is designed to ensure the integrity of a software product from initiation to end-user installation.”

[6] https://langfuse.com/docs
> “Langfuse is an open source LLM engineering platform. Trace, evals, prompt management.”

[7] https://docs.smith.langchain.com/
> “LangSmith is a platform for building production-grade LLM applications.”

[8] https://www.helicone.ai/docs
> “Helicone is an open-source observability platform for LLM applications.”

[9] https://opentelemetry.io/docs/specs/semconv/gen-ai/
> “Generative AI semantic conventions have moved to the OpenTelemetry GenAI semantic conventions repository.”

[10] https://opentelemetry.io/docs/specs/semconv/gen-ai/
> “This page has moved and is no longer maintained in this repository.”

[11] https://docs.deno.com/runtime/fundamentals/security/
> “Be aware that sub-processes are not run with the same permissions as the deno process.”

[12] https://github.com/LavaMoat/LavaMoat
> “LavaMoat is a set of tools for sandboxing dependencies in Node.js.”

[13] https://github.com/containers/bubblewrap
> “bubblewrap is a tool for unprivileged containerization and sandboxing.”

[14] https://www.kernel.org/doc/html/latest/security/landlock/index.html
> “Landlock is a stack of technologies aimed to empower any process to restrict itself.”

[15] https://e2b.dev/docs
> “E2B is a secure cloud environment for running AI-generated code.”

[16] https://vercel.com/docs/sandbox
> “Vercel Sandbox is a runtime for AI agents.”

[17] https://microsandbox.dev/
> “microsandbox is an open-source, self-hosted sandbox for AI agents and coding assistants.”

[18] https://docs.sigstore.dev/
> “Sigstore is a project that provides tools and services for signing, verifying, and protecting software.”

[19] https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations
> “Artifact Attestations allow you to generate verifiable claims about your software artifacts.”

[20] https://bazel.build/docs/sandboxing
> “Bazel uses sandboxed execution to ensure build correctness and reproducibility.”

[21] https://nixos.org/manual/nix/stable/
> “Nix is a purely functional package manager that makes builds more reproducible.”

[22] https://rr-project.org/
> “rr is a lightweight tool for recording, replaying and debugging execution.”

[23] https://reprotest.readthedocs.io/
> “reprotest builds the same source code twice in different environments.”

[24] https://github.com/nektos/act
> “Run your GitHub Actions locally.”

[25] https://www.jenkins.io/doc/pipeline/steps/junit/
> “junit: Archive JUnit-formatted test results.”

[26] https://learn.microsoft.com/en-us/visualstudio/test/trx-report?view=vs-2022
> “The TRX file is a test result file generated by the .NET test platform.”

[27] https://www.163.com/dy/article/LB58R2AO05561FZE_pdya11y.html
> “这个工具叫 honestly。”

[28] https://www.sohu.com/a/20260324A01YE900
> “claude-tap是一个本地代理和Trace查看器。”

[29] https://thepaper.cn/newsDetail_forward_31588982
> “这种策略使其能够自然地映射到 token 级别的标签，从而实现实时流式检测。”
