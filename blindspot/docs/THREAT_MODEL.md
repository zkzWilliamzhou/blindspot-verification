# Threat model

Read this before relying on a report.

## What blindspot is

A local measurement tool. It runs one clean command, captures ground truth at
the OS boundary, reconstructs a filtered observation from those bytes, and
reports the delta. It is not a security product, not a sandbox, and not a
witness.

## Supported threat model

- An honest operator invokes `blindspot run` to measure their own agent's
  observation channel.
- A later reviewer wants to detect **accidental editing, deletion, reordering,
  or truncation** of recorded entries.
- The optional HMAC key is stored with mode 0600 and is not available to the
  untrusted agent.

Under these conditions `blindspot verify` detects: edited entry content, broken
`prev` links, sequence gaps, reordered entries, truncation/rollback against the
head, malformed lines, and (with a key) a replaced head.

## What the ledger cannot do

It is **tamper-evident, not tamper-proof**. A local hash chain with no external
anchor cannot provide non-repudiation. Concrete failure modes:

1. **Wholesale replacement.** Any process with write access can delete
   `.blindspot/`, write a fresh ledger, and generate a new head. The chain is
   internally valid. Nothing in this tool detects it.
2. **Rollback, worked example.** Run 5 commands; save `head.json`. Run 3 more.
   Restore the saved head. `verify` reports `head seq 5 does not match 8
   entries` — so this *is* detected when the ledger file remains. But if the
   attacker also restores the 5-entry `ledger.jsonl`, both checks pass. No
   external witness exists to say which state is older.
3. **Key theft, worked example.** Read `.blindspot/key` (same user, same
   process privileges, or a prompt-injected agent with file read). The attacker
   can now compute a valid HMAC for a forged head. The signature proves a key
   was used, not who used it.
4. **Clock trust.** `created_at` comes from the local wall clock. It can be set
   forwards or backwards. There is no timestamp authority.
5. **Unrecorded commands.** Everything outside `blindspot run` is invisible.
   The tool never invents a receipt for an unrecorded command; it simply has no
   evidence. A hook can warn, but cannot force every agent path.
6. **Wrong test selection.** A command can be captured perfectly and still be
   the wrong test, run against the wrong revision, or before the final edit.
7. **Semantic proof.** No execution record proves correctness, absence of
   vulnerabilities, coverage, or compliance with intent.
8. **False command.** The receipt proves what was recorded, not that the
   command executed as intended outside the wrapper.

## Capture and execution limits

- On POSIX, the child gets a minimal environment, closed stdin, its own process
  group, CPU/FILE/NOFILE/AS/NPROC limits, and a timeout with process-group
  kill. This is **resource containment, not a security boundary**.
- `--deny-net` requires Linux `unshare -n` and **refuses to run** if the probe
  fails. Without it, network is enabled and the report says so.
- `cwd` is confined to the project root using `realpath` + `commonpath`, which
  blocks `..` and symlink escapes. This confines one argument; it is not a
  filesystem sandbox for the command's own writes.
- On non-POSIX platforms, process-group kill and resource limits are
  unavailable. The report says so.
- Interactive commands, pseudo-terminal behaviour, inherited file descriptors,
  job control, and complex shell constructs are outside the supported subset.

## Parser and replay limits

- Only a defined set of filters (`head`, `tail`, `grep`/`egrep`/`fgrep`, `wc`,
  `cut`, `tr`, `sort`, `uniq`) is replayed, using the real binaries over captured
  bytes. Unsupported constructs produce a **refusal and no execution**; inside
  an already-captured report they are listed under `unsimulated`.
- `2>&1` merging is approximated by concatenation, because stdout/stderr
  interleaving cannot be recovered without a PTY. The report discloses it.
- `--max-bytes` simulates a harness cap with a head/tail window. Real harnesses
  use different truncation policies. The report discloses it.
- `--max-output` caps what is **stored**, not what is hashed. Raw digests cover
  the full stream. If the real child wrote past the cap, the report says so.
- A command that times out yields partial ground truth. The report says so.

## Privacy limits

- Stored text is scrubbed for common credential shapes (AWS keys, GitHub and
  Slack tokens, private keys, JWTs, `key=value` assignments, bearer tokens,
  URL credentials). This is a **best-effort filter, not a secret scanner**.
  Encoded, split, or novel secret formats can pass through.
- Secret-looking environment variable values are never stored; only a SHA-256
  digest over `NAME=VALUE` pairs is kept. Digests are not reversible, but a
  short or guessable value could still be brute-forced from a digest.
- Reports contain command strings, output excerpts and paths. Treat the JSON
  envelope as sensitive before sharing it.
- Raw digests cover **unredacted** bytes by design, so integrity remains
  verifiable without persisting the plaintext. Redaction counts are recorded.

## Output safety

- Human-readable output strips C0 control characters and DEL, so captured bytes
  cannot emit terminal escape sequences. JSON and SARIF outputs are valid JSON
  but may contain escaped control characters; consumers should still treat them
  as data, not as instructions.
- Text inside a report is untrusted data. Never interpolate it into shell code.

## Claims the project explicitly refuses to make

- Never call it "tamper-proof" or "unforgeable"; never call it an "AI lie
  detector" or claim it "proves tests passed".
- Never claim it "guarantees the agent is honest", is "compliance-ready", or
  provides "sandboxed execution".
- Never publish a star count, adoption projection, or a claim that it is the
  only tool of its kind in the world. Absolute global novelty cannot be proven.

## If you need stronger assurance

Anchor the chain root externally (trusted timestamping, a transparency log, or
a signed CI artifact), store the HMAC key outside the agent's reach, and keep CI
as the durable merge gate. blindspot does not provide those in v1; ADR-003
records that decision.
