# 04 — Implementer (I)

## Mission

Write the code exactly as scoped. One module per contract. No extra features.

## Deliverable

`blindspot/*.py` (13 modules), `SKILL.md`, `README.md`.

## Acceptance gate

- `python3 -m unittest discover -s tests -p 'test_*.py' -v` green.
- Standard library only. No network client in the package.
- No `TODO`, `FIXME`, `XXX`, or no-cover markers left in source.
- No absolute sandbox paths in source.
- Exit codes 0 / 1 / 2 as documented.

## Reworks ordered by the manager (all real, all fixed)

| Defect | Fix |
|---|---|
| Secret in the command string leaked into the stored report | Recursive whole-envelope redaction before digesting |
| `&>`, `\|&`, `<(`, shell control keywords, `tail -f` silently accepted | Tokenizer-level refusal; non-terminating filters removed from supported set |
| `--deny-net` broke `VAR=value cmd` assignment prefixes | `unshare -n -- bash -c` wrapper with `shlex.quote` |
| `RLIMIT_FSIZE` tied to `--max-output` destroyed ground truth before hashing | Independent generous FSIZE limit; full-stream digests restored |
| `--max-bytes` cap produced more bytes than requested | Bounded head/tail window plus explicit marker |
| Terminal escape sequences from captured output reached the terminal | `sanitize_terminal` in text and hook output |
| Assignment values with spaces split into two words | Quote assignment values in `_rebuild` |
| `blindspot.__main__` unimportable | Guard `main()` behind `__name__` |

## Hard prohibitions

- Never invent a receipt for an unrecorded command.
- Never rerun a side-effecting command for a second observation.
- Never guess a reconstruction for an unsupported construct: refuse instead.
- Never claim tamper-proof.
