# Vercel Labs agent skills — reference notes (RECONSTRUCTED)

Sources: `github.com/vercel-labs/agent-skills` ("Vercel's official collection of
agent skills") and `github.com/vercel-labs/skills` ("the open agent skills tool —
npx skills", TypeScript). Repository pages could not be fetched directly; the
skill list below comes from a public mirror of the README.

## Catalogue

| Skill | What it does |
|---|---|
| `vercel-optimize` | Audits a Vercel project for cost, performance, reliability, caching, function usage and billing. Collects metrics first, then investigates only the routes those metrics point to. |
| `react-best-practices` | 40+ React/Next.js performance rules across 8 categories, prioritized by impact: accessibility, focus states, forms, animation, typography, images, performance, navigation/state, dark mode, touch, i18n. |
| `writing-guidelines` | Reviews docs and prose against the Vercel writing handbook, 80+ rules on voice, structure, content types, code samples, typography, AI workflow. |
| `react-native-guidelines` | 16 rules across 7 sections for React Native/Expo: performance, layout, animation, images, state, architecture, platform specifics. |
| `react-view-transitions` | Smooth native-feeling animations with React's View Transition API, including Next.js integration. |

`vercel-labs/skills` is the `npx skills` CLI used to install skills across
harnesses; `skills.sh` is the distribution page. It was unreachable here.

## Applied here

The `vercel-optimize` idea of "collect metrics first, then investigate only what
they point to" shaped `tests/audit_harness.py`: probes are grouped by real risk
areas rather than scanning every file with generic heuristics. The writing
guidelines' bias toward user-shaped titles and direct statements shaped the
README's opening ("Your agent only saw the last line") rather than an abstract
mission statement.

## Status

NOT installed. `npx skills add ...` impossible (npm registry returned 403).
This file is a summary, not upstream content.
