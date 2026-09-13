<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Changelog

All notable changes to the Spec-Agentic-SDLC corpus are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the version of record is
`version.txt` (ADR-0057) and follows SemVer. Governance-relevant changes cite the ADR that
authorises them.

## [Unreleased]

### Added

- `LICENSE` (MIT), `CITATION.cff` and a README license section (#2).
- `version.txt` (1.0.0) and this changelog (#3).
- `scripts/bash/adopt.sh` — copy the minimal / governed / full layer into a product repository
  (`--here`, `--integration`, `--force`, `--dry-run`, `--json`); ADR-0091 (#16).
- `check-corpus.sh` C8: governance invariants asserted (tests-first template, no git side effects
  in scripts, constitution articles and version line, PreToolUse guard, `--require-approved`) (#15).
- `scripts/python/adopter_paths.py` (check / inventory / mark) and the generated
  `docs/reference/adopter-provided-paths.md`; every file naming an adopter-provided path now
  carries the `adopter-paths` marker, enforced as `check-corpus.sh` C7 (#14).
- `tests/scripts/test_scripts.sh`: 43 behavioural tests of the bash scripts (numbering, slugs,
  feature resolution, approval gate, plan setup, tasks-to-issues), run by `check-corpus.sh` (#13).
- `.github/workflows/corpus-check.yml` (check-corpus.sh, markdownlint-cli2, guard self-test on
  every push and PR), `.markdownlint-cli2.jsonc`, `.github/CODEOWNERS` (#12).
- `scripts/bash/check-corpus.sh`: internal links, spec frontmatter against the schema, ADR index
  and numbering, script syntax and smoke runs on the example bundle, high-risk-guard self-test (#11).
- `/sdd-taskstoissues` skill and `scripts/bash/tasks-to-issues.sh` (gh CLI; approved spec only;
  dedup by task id; issue number written back to tasks.md) (#10).
- Worked example of the feature bundle: `specs/features/SPEC-LGS-001-log-based-golden-signals/`
  (spec, plan, research, data-model, contracts, quickstart, requirements checklist, tasks); the
  flat `SPEC-LGS-001-golden-signals-feature-spec.md` is `superseded` by it (#5).

### Changed

- markdownlint pass over the corpus: blank lines around fences/lists/headings, consistent
  emphasis style, one malformed reference link, heading levels in `docs/troubleshooting.md` (#12).
- `specs/spec-frontmatter.schema.json` id pattern now admits digits in the domain code
  (`SPEC-K8S-001`, listed in ADR-0085); the `feature-spec-lint` gate uses the same pattern (#11).
- `SETUP.md` is now the corpus adoption guide (layers minimal/governed/full, adopter-provided
  paths, Claude Code wiring); the product template's SETUP is archived under
  `docs/reference/repository-template-v2-SETUP.md` (#9).
- `/sdd-plan`, `/sdd-analyze`, `/sdd-tasks`, `/sdd-implement` now treat `services.yaml`, `src/…`
  and `make` targets as adopter-provided and conditional; `.claude/skills/README.md` documents the
  rule (#8).
- `templates/research-template.md`, `data-model-template.md`, `quickstart-template.md`,
  `contracts-README-template.md` added; `setup-plan.sh` copies all five plan artefacts and
  `/sdd-plan` cites them (#7).
- `specs/features/` uses one convention: `<SPEC-ID>-<slug>/spec.md` bundles. SPEC-FEAT-001 moved
  from `FEAT-001/feature-spec.md`; README, process docs, gates, agents, issue templates and the
  `feature-spec-lint` harness gate updated; `.github/FEATURE_SPEC_TEMPLATE.md` marked legacy (#6).
- `CLAUDE.md` 2.9.0 (2026-09-12): §3 now maps each subsection to the constitution article it
  condenses and states the constitution's precedence; `CLAUDE_SESSION_INIT.md` rewritten for
  the corpus (identity, corpus-vs-adopter paths, critical paths, `/sdd-*` quick reference) (#4).

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
