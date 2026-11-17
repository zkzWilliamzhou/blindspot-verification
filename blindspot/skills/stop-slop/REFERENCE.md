# stop-slop — prose rules (RECONSTRUCTED)

Primary upstream: `github.com/hardikpandya/stop-slop` (MIT, Hardik Pandya).
A separate Chinese-language skill `tomerose/stop-slop` also exists. The
repository could not be cloned (git clone returned 403). Rules below come from
public mirror pages describing the SKILL.md and its `references/` files.

## Core rules applied to README and docs

1. **Cut filler phrases.** Remove throat-clearing openers, emphasis crutches,
   and adverbs. See `references/phrases.md` upstream.
2. **Break formulaic structures.** Avoid binary "not X, it's Y" contrasts,
   negative listings, dramatic fragmentation, rhetorical setups, false agency.
3. **Use active voice.** Every sentence needs a human subject doing something.
   No passive constructions, no inanimate object performing a human action.
4. **Be specific.** Name the specific thing. No vague declaratives ("The
   reasons are structural"), no lazy extremes doing vague work.
5. **Put the reader in the room.** "You" beats "People". Specifics beat
   abstractions.
6. **Vary rhythm.** Mix sentence lengths. Two items beat three. End paragraphs
   differently.
7. **No em dashes.** Trust readers. State facts directly.
8. **Cut quotables.** If it sounds like a pull-quote, rewrite it.

Quick checks before delivering prose: any adverbs, passive voice, inanimate
thing doing a human verb, Wh- opener, "here's what/this/that" throat-clearing,
"not X, it's Y", three consecutive sentences of matching length, punchy
one-liner paragraph ending, em dash, vague declarative, narrator-from-a-distance,
meta-joiners.

One mirror describes a different, linter-oriented evolution of the same repo
(`scripts/slopcheck.mjs`, Node 20+, deterministic phrase rules, scores as
penalties 0–100, `--baseline` comparison). That variant was **not** used here;
we could not fetch or verify the script.

## Where we deliberately did not follow it

Technical documentation sometimes needs adverbs like "deliberately" and
"exactly", and the threat model needs "cannot". The rule "kill every adverb" was
treated as guidance, not law. Quotes in the research reports were left intact.

## Status

NOT installed. Rules applied manually from mirrored descriptions.
