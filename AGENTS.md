# AGENTS.md — Instructions for AI Coding Agents

> **Documentation-corpus edition (Spec-Agentic-SDLC).** This repository is a documentation,
> governance and agent-operating corpus — no application code. Paths such as `src/…`,
> `scripts/governance/…`, `.github/workflows/ci.yml` and `make` targets that appear inside the
> corpus describe the product repository that adopts it (`docs/reference/adopter-provided-paths.md`).
> The normative core is `memory/constitution.md`; the workflow commands are `/sdd-*`.

This file is the cross-tool contract for AI coding agents working **in this repository** or in
a repository that adopted it. It says exactly what each agent receives, what it must never do,
and how to validate a change. Claude Code users: `CLAUDE.md` is the deeper, authoritative
behavioural contract and `CLAUDE_SESSION_INIT.md` the session primer — read both.

## 1. What each agent receives (ADR-0091)

| Agent           | Commands                                                            | Location                          | Also gets                                                       | Does **not** get                                                                 |
| --------------- | ------------------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Claude Code     | `/sdd-*` (10) + `/deliver` + one skill per `skills/**/*.md`         | `.claude/skills/` (canonical)     | `CLAUDE.md`, delivery subagents (`.claude/agents/`), personas, **PreToolUse high-risk-action guard** and **UserPromptSubmit sdd-gate** (`.claude/settings.json`, ADR-0092) | —                                                                                |
| GitHub Copilot  | `sdd-*` (10), rendered                                              | `.github/skills/<name>/SKILL.md`  | this file                                                       | `/deliver`, delivery subagents, personas, the PreToolUse guard and the sdd-gate |
| Cursor          | `sdd-*` (10), rendered                                              | `.cursor/skills/<name>/SKILL.md`  | this file                                                       | same as Copilot                                                                  |
| Codex CLI       | `sdd-*` (10), rendered (`$sdd-<name>`)                              | `.agents/skills/<name>/SKILL.md`  | this file                                                       | same as Copilot                                                                  |
| Gemini CLI      | `sdd-*` (10), rendered as TOML (`{{args}}`)                         | `.gemini/commands/<name>.toml`    | this file                                                       | same as Copilot                                                                  |
| Any other agent | none                                                                | —                                 | this file                                                       | everything above; follow §3–§5 by hand                                           |

The rendered copies are generated from `.claude/skills/sdd-*/SKILL.md` by
`scripts/bash/render-commands.sh`; never edit a copy (`check-corpus.sh` C9 rejects drift).
Agents without the two hooks must apply §5 themselves: the PreToolUse guard denies
push/merge/release/deploy for subagents and asks in the main session, and the sdd-gate blocks
`/sdd-plan`, `/sdd-tasks`, `/sdd-implement` and `/sdd-taskstoissues` on an unapproved spec — other
tools have no equivalent enforcement here.

## 2. Repository orientation

- `memory/constitution.md` — root of authority (nine articles; I, II, V, VII, IX protected)
- `CLAUDE.md` — operating contract · `CLAUDE_SESSION_INIT.md` — primer · `SETUP.md` — adoption guide
- `version.txt` — version of record (ADR-0057) · `CHANGELOG.md` · `docs/adr/` — binding decisions (ADR-0001…)
- `specs/features/<SPEC-ID>-<slug>/` — feature bundles (spec, plan, tasks, …; ADR-0085, ADR-0090)
- `templates/`, `scripts/bash/`, `scripts/python/` — what the `/sdd-*` commands execute
- `docs/process/WORKFLOW.md` — 15-phase lifecycle · `docs/sdlc/spec-kit-comparison.md` — why the commands are shaped as they are

## 3. Files that must not be edited casually

| File / directory                                   | Why                                                                                   |
| -------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `memory/constitution.md`                           | Protected articles may only be strengthened; amendment = version bump + Sync Impact Report (`/sdd-constitution`) |
| `docs/adr/`                                        | ADRs are decisions of record; append/supersede, never rewrite; keep `README.md` index and numbering contiguous |
| `specs/`                                           | Specs are reviewed before the code they describe; only a human sets `status: approved` |
| `.claude/hooks/`, `.claude/settings.json`          | High-risk-action guard — Security + AI Governance approval                            |
| `.claude/skills/sdd-*/`                            | Source of the workflow commands; re-render after any edit                             |
| `.github/skills/`, `.cursor/skills/`, `.agents/skills/`, `.gemini/commands/` | Generated — edit the source, not the copy                    |
| `CLAUDE.md`, `AGENTS.md`                           | Behavioural contracts — team sign-off; keep in step with the constitution             |
| `.github/workflows/`                               | The corpus's own CI (`corpus-check.yml`) — DevOps Lead                                |
| _(adopting repository)_ `src/guardrails/`, `src/agents/hitl_gateway.py`, `infrastructure/feature-flags/` | Weakening guardrails, HITL or autonomy needs the reviews named in `CLAUDE.md` §8 |

## 4. Required workflow before changes

1. Read `memory/constitution.md`; read the linked spec before writing anything the spec governs.
2. Feature work runs through the commands, in order: `/sdd-specify` → `/sdd-clarify` →
   _Spec-as-PR approval_ → `/sdd-plan` → `/sdd-checklist` → `/sdd-tasks` → `/sdd-analyze` →
   `/sdd-implement` ⇄ `/sdd-converge` → PR. Every command names the human gate it stops at.
3. Check whether an ADR already covers a decision; if not, propose one from `docs/adr/ADR-TEMPLATE.md`.
4. **Task sizing — the 2-skill budget (ADR-0060).** Every task loads at most 2 repo skills
   (`skills/<domain>/<name>.md`). If a task would need a 3rd, split it at the skill boundary.
   One task = one reviewable artefact. `CLAUDE.md` and repo context are ambient and never count.
5. Run the validation commands in §7 before pushing.

## 5. What AI agents must never do

- Do not commit or log real secrets, tokens, or PII.
- Do not set `status: approved` on a spec, merge a PR, push to a protected branch, create a
  release, deploy, or change an autonomy flag — those are human gates (Constitution V, ADR-0058).
- Do not weaken a protected constitution article, a guardrail, a test, or the abuse-case count.
- Do not add `--no-verify` to git commands; do not add `# nosec` / `# noqa` without justification.
- Do not remove or alter existing ADRs — supersede them.
- Do not invent an API, path, ADR number or config key; write `uncertain — verify` (Constitution IX).
- Do not write code that references a spec that does not exist yet, or one that is not `approved`.

## 6. How to update ADRs

ADRs are **append-only**. Create a new ADR for a new decision; to change a past decision, add a
new ADR and mark the old one `Superseded by ADR-NNNN` in place. Add every new ADR to
`docs/adr/README.md` (C3 of `check-corpus.sh` fails on a missing row or a numbering gap) and to
the quick index in `CLAUDE_SESSION_INIT.md`.

## 7. Validation commands (run before pushing)

```bash
scripts/bash/check-corpus.sh          # links · frontmatter · ADR index · scripts · tests · markers · rendered copies · guard
npx --yes markdownlint-cli2@0.17.2    # the same lint CI runs
python3 .claude/hooks/verify-high-risk-guard.py
scripts/bash/render-commands.sh       # after editing any .claude/skills/sdd-*/SKILL.md
```

In an adopting product repository, add that repository's own gates (its `make` targets or CI).

See also: [`CLAUDE.md`](CLAUDE.md) · [`SETUP.md`](SETUP.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`.claude/skills/README.md`](.claude/skills/README.md)
