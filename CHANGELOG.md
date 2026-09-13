# Changelog

All notable changes to the Spec-Agentic-SDLC corpus are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the version of record is
`version.txt` (ADR-0057) and follows SemVer. Governance-relevant changes cite the ADR that
authorises them.

## [Unreleased]

### Added

- `LICENSE` (MIT), `CITATION.cff` and a README license section (#2).
- `version.txt` (1.0.0) and this changelog (#3).

## [1.0.0] — 2026-09-12

### Added

- Corpus extracted from Repository-Template-v2 (branch `feat/W15-test-depth`, Waves 11–15):
  Markdown documentation, harness YAML, control-matrix YAML/JSON and the `.claude/` operating
  layer. No application code.
- `memory/constitution.md` v1.0.0 — nine binding articles condensed from `CLAUDE.md` §3
  (ADR-0090).
- Feature-directory bundle `specs/features/<SPEC-ID>-<slug>/` and executable templates for
  spec, plan, tasks, checklist, roadmap and constitution under `templates/` (ADR-0090).
- Nine Claude Code commands `/sdd-constitution`, `/sdd-specify`, `/sdd-clarify`, `/sdd-plan`,
  `/sdd-checklist`, `/sdd-tasks`, `/sdd-analyze`, `/sdd-implement`, `/sdd-converge` under
  `.claude/skills/sdd-*/` (ADR-0090).
- Helper scripts `scripts/bash/{common,create-new-feature,check-prerequisites,setup-plan}.sh`
  with JSON output, per-domain SPEC-ID numbering and no git-branch side effects (ADR-0090).
- `docs/sdlc/spec-kit-comparison.md` and `docs/sdlc/spec-persistence-model.md`.
- ADR-0090 — Adopt spec-kit workflow primitives.

### Upstream reference

- github/spec-kit pinned at commit `d848fb4` (2026-09-11, release v1.0.6). Adoption,
  adaptation and deliberate omissions are recorded in `docs/sdlc/spec-kit-comparison.md`.

[Unreleased]: https://github.com/valdomirosouza/Spec-Agentic-SDLC/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/valdomirosouza/Spec-Agentic-SDLC/releases/tag/v1.0.0
