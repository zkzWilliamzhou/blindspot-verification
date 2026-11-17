---
name: blindspot
description: Check a shell command for observation-degrading constructs before using its output to claim that tests passed, a build succeeded, or an action completed. Use when an agent is about to run a Bash command that will be used as evidence of success.
license: MPL-2.0
compatibility: Requires Python 3.10+ and the blindspot package. No network, API keys, or third-party dependencies.
---

# blindspot

An agent reads the output of the shell commands it writes. Those commands often
destroy the evidence they run on. `pytest | tail -1` hides the failure list and
replaces the exit status with `tail`'s zero. `npm test || true` discards the real
exit code. `make 2>/dev/null` hides every compiler error.

Use this skill before reporting any result that depends on command output.

## When to use

- Before stating "tests pass", "the build succeeds", "no errors", or "done".
- When a command contains a pipe, a redirection to `/dev/null`, `|| true`,
  `; true`, `set +e`, or an output cap.
- When you are about to paste a filtered or truncated command result into a
  summary.

## Procedure

1. Run `blindspot inspect "<your command>"` first. It never executes anything.
2. If it reports a critical degradation, rewrite the command so the full result
   reaches you. Prefer running the plain command and reading its full output.
   Keep `set -o pipefail` when a pipeline is genuinely needed.
3. If you must keep the filtered command, run `blindspot run "<command>"` and
   read the delta. It executes the clean command once and reconstructs the
   filtered view from captured bytes.
4. If the verdict is `MISLEADING`, do not claim success. Report the hidden
   lines and the real exit status, then fix the cause and rerun.
5. If the command was refused, do not execute it through another path and then
   claim it was checked. Say that the observation channel could not be
   verified.

## What this skill does not do

It does not verify correctness, intent, coverage, or test quality. It does not
read your prose and does not detect lies. It measures how much of the real
execution reached your context. CI remains the durable merge gate.

## Commands

```
blindspot inspect "pytest -q | tail -1"
blindspot run "pytest -q | tail -1"
blindspot verify
blindspot hook --strict
```

## Hard rules

- Never state success based on output you know was filtered or truncated.
- Never add `|| true` to make a check pass.
- Never pipe a test summary through `head` or `tail` and then quote it as the
  full result.
- A refused or unverified command stays unverified. Do not invent evidence.
