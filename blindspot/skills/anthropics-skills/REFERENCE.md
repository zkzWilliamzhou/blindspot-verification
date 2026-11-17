# anthropics/skills — reference notes (RECONSTRUCTED)

Source: `https://github.com/anthropics/skills`. Retrieved through the public
GitHub README mirror via web fetch; the repository itself could not be cloned.

## Format (the part used in this project)

A Skill is a folder containing a `SKILL.md` file, plus optional scripts and
resources. `SKILL.md` has YAML frontmatter with two required fields:

- `name` — lowercase, hyphens for spaces, unique identifier.
- `description` — a complete description of what the skill does and **when to
  use it**.

The body is Markdown instructions. The skill is loaded on demand when a task
matches, so an idle skill costs no tokens. Repository layout:

```
skills/     Creative & Design, Development & Technical,
            Enterprise & Communication, Document Skills
spec/       Agent Skills specification
template/   minimal skill template
```

Document skills (`docx`, `pdf`, `pptx`, `xlsx`) are source-available rather than
open source. Many other skills are Apache-2.0.

Installation in Claude Code is via the plugin marketplace:
`/plugin marketplace add anthropics/skills`, then
`/plugin install example-skills@anthropic-agent-skills` or
`/plugin install document-skills@anthropic-agent-skills`.

## Applied here

The root `SKILL.md` of blindspot follows this folder-plus-frontmatter format and
puts the trigger condition ("before stating tests pass / build succeeds / done")
into the `description`, exactly as the format requires.

## Status

NOT installed. No files from the upstream repository were vendored. This file
is a summary, not upstream content.
