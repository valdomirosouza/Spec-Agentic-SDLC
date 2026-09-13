# ADR-0091 — Corpus Adoption via `adopt.sh` and Rendered Per-Agent Skill Copies

**Status:** Accepted
**Date:** 2026-09-12
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — operational policy for distributing the corpus (`SETUP.md`)
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0090](ADR-0090-adopt-spec-kit-workflow-primitives.md) (spec-kit primitives), [ADR-0060](ADR-0060-task-atomicity-skill-budget.md) (skill budget), [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation)

---

## Context

The spec-kit comparison of 2026-09-12 scored this corpus 2.5/10 on bootstrapping and 3/10 on
agent portability: there was no equivalent of `specify init --here`, `SETUP.md` described a
product template rather than the corpus, and although `AGENTS.md` promised Copilot and Cursor
support, every executable artefact (`.claude/skills/`, `.claude/agents/`, the PreToolUse hook)
existed only for Claude Code. spec-kit v1.0.6 solves both with a Python CLI (`specify`) that
renders one command template into the layout of 30+ agents, most of them now **skills-based**:
`.claude/skills`, `.github/skills` (Copilot), `.cursor/skills`, `.agents/skills` (Codex) and
`.gemini/commands` (Gemini CLI, TOML).

Constraints: the corpus must stay copy-in-place (no runtime dependency beyond bash 3.2 and
python3), must never overwrite an adopter's files silently, must never run git commands on the
adopter's behalf (Constitution V), and must keep `.claude/skills/sdd-*/SKILL.md` as the single
source of truth so the nine-plus-one commands cannot drift between agents.

## Decision

1. **`scripts/bash/adopt.sh`** is the corpus's `init`. It copies one of three layers
   (`minimal` — workflow only; `governed` — plus lifecycle, ADRs, control matrices, harness,
   templates; `full` — the complete corpus) into `--here` or a target directory, adds the
   requested `--integration` directories, never overwrites without `--force`, never deletes,
   never runs git, and prints a manifest (`--json`). A bash script is chosen over a Python CLI
   because the corpus ships no package, and over `git subtree`/submodules because adopters
   merge `CLAUDE.md`/`AGENTS.md` with their own rather than tracking ours verbatim.
2. **Per-agent copies are rendered, not hand-maintained.** `scripts/bash/render-commands.sh`
   reads `.claude/skills/sdd-*/SKILL.md` and writes `.github/skills/sdd-*/SKILL.md` (Copilot),
   `.cursor/skills/sdd-*/SKILL.md` (Cursor), `.agents/skills/sdd-*/SKILL.md` (Codex) and
   `.gemini/commands/sdd-*.toml` (Gemini CLI, `$ARGUMENTS` → `{{args}}`). The rendered files are
   committed so an adopter gets them by copying, and `check-corpus.sh` fails when they are stale
   (re-render produces a diff). Claude Code remains canonical; a change to a command is a change
   to its `SKILL.md`, followed by a re-render.
3. **What is not portable is said so.** The PreToolUse high-risk-action guard and the
   `.claude/agents/` delivery subagents are Claude Code features; `AGENTS.md` lists per agent
   exactly what it receives and what it does not.

## Consequences

### Positive

- An empty directory becomes a working `/sdd-*` workspace with one command; the ten-minute check
  in `SETUP.md` §0 is reproducible on any adopter.
- Copilot, Cursor, Codex and Gemini users get the same nine-plus-one commands, generated from one
  source; drift is caught in CI.
- No new runtime: bash 3.2, python3, and the tools the adopter already has.

### Negative / Trade-offs

- Rendered copies quadruple the number of command files in the repository; reviewers must
  remember that only `.claude/skills/` is edited by hand (C9 enforces it).
- Only the command layer is portable. The hook-based guard, personas and delivery agents stay
  Claude-specific until the other tools expose equivalent extension points.
- Gemini's TOML format is followed as spec-kit renders it; if Gemini CLI changes its command
  schema the renderer, not the skills, must change.

## Alternatives Considered

- **Install spec-kit's `specify` CLI and register this corpus as a preset/bundle** — rejected:
  ADR-0090 §4 already declined the extension engine; the corpus's commands diverge from
  spec-kit's (mandatory tests, approval gate, escalation) and would have to be maintained as
  overrides of upstream templates.
- **Hand-write per-agent files** — rejected: four copies of ten prompts drift within a release.
- **Publish the corpus as a package (PyPI / npm)** — rejected for now: no adopters outside the
  organisation; revisit when there are (ADR-0090 §4 sets the same trigger).
- **Git submodule** — rejected: adopters edit `CLAUDE.md`, `AGENTS.md` and the constitution;
  a submodule cannot be edited in place.

## Compliance & Risk

- **Controls affected:** none — documentation tooling.
- **Data classification impact:** none.
- **Autonomy impact:** none; `adopt.sh` and `render-commands.sh` run no git command and touch no
  feature flag (asserted by `check-corpus.sh` C8).
- **Review/expiry:** revisit when an integration changes its skill/command layout or when an
  external adopter appears.

---

## Related

- `SETUP.md` — the adoption guide the script implements
- `docs/reference/adopter-provided-paths.md` — what the adopting repository supplies
