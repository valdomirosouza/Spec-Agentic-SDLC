# `.claude/skills/` — the `/`-command layer

Each directory is a Claude Code skill (`SKILL.md` with `name` and `description` frontmatter).
Two families live here:

| Family                          | Skills                                                                                                                   | Source of truth                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| Spec-kit-style workflow (ADR-0090) | `sdd-constitution`, `sdd-specify`, `sdd-clarify`, `sdd-plan`, `sdd-checklist`, `sdd-tasks`, `sdd-analyze`, `sdd-implement`, `sdd-converge`, `sdd-taskstoissues`; `deliver` for the 15 phases | `memory/constitution.md`, `templates/`, `scripts/bash/` |
| Domain skills (`/`-command copies) | `pii`, `gdpr`, `lgpd`, `owasp-top10`, `otel`, `golden-signals`, `prr`, `rest-api-design`, … (one per `skills/**/*.md`) | `skills/` (plain Markdown; load ≤ 2 per task — ADR-0060) |

## Adopter-provided paths

This repository is a documentation corpus. The `sdd-*` skills are written to run **inside a
product repository that adopted the corpus**, so they may mention paths and commands that only
exist there. Every such mention is conditional ("when the adopting repository has one"); a skill
never *requires* a file this corpus does not ship.

| Mentioned by the skills            | Provided by                               | What the skill does when it is absent            |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------ |
| `services.yaml` (service/topic registry) | adopting repository                 | skips the topic-registration check               |
| `src/agents/`, `src/guardrails/`   | adopting repository (AI Agents extension) | the related hard stops and abuse-case tasks do not fire |
| `make` targets / CI gates          | adopting repository                       | "gates green" means that repository's own gates   |
| `CLAUDE_SESSION_INIT.md`, `memory/constitution.md`, `templates/`, `scripts/bash/`, `docs/`, `specs/` | **this corpus** | always present                                   |

The full corpus-vs-adopter split is in `CLAUDE_SESSION_INIT.md` and `SETUP.md`.
