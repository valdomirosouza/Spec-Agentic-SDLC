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
- `specs/data/data-quality.md` — the six dimensions with one operational definition each, the rule
  shape, severity and response, data SLOs in the same form as the service SLOs, observability with
  masked violation samples, the five points where quality is checked, and data incidents with a
  rule ratchet (#29).
- `docs/data/data-governance-charter.md` — scope, seven principles, the data owner / steward /
  custodian split, the data governance council with decision rights and two vetoes, the path a
  dataset takes to become governed, time-boxed exceptions, and an honest table of what is enforced
  versus review-only; RACI matrix §5 Data Governance added with 16 processes (#28).
- `specs/compliance/ai-post-market-monitoring.md` — EU AI Act Art. 72 monitoring plan (four signal
  families, thresholds, cadence, ownership) and the Art. 73 serious-incident procedure, including
  the near-miss rule and the refusal to invent a reporting authority (#27).
- `docs/ai-governance/nist-ai-rmf.md` rewritten by category identifier (GOVERN 1–6, MAP 1–5,
  MEASURE 1–4, MANAGE 1–4; 19 categories, 72 subcategories), with a declared use-case profile,
  coverage and gap per category, and only verified subcategory ids cited; REM-019 opened (#26).
- `docs/compliance/iso42001-scope-and-soa.md` (scope, interested parties, clauses 4–10, Statement
  of Applicability over the nine Annex A objectives, certification posture) and
  `iso42001-annex-a-control-matrix.md`; REM-015 to REM-018 opened for the clause 6, 9, 10 and A.2
  gaps (#25).
- `specs/compliance/eu-ai-act-control-matrix.yaml` — 17 obligations (Art. 5, Arts. 9–17 and 20,
  Arts. 43/47/48/49, Art. 50, Arts. 51–55, Arts. 72–73, Annex IV) with owner, status, gate,
  application date and gap; `adopter:` and `planned:#issue:` path prefixes; the compliance page
  rewritten as its human reading (#24).
- ADR-0093 — EU AI Act role (provider of the system + deployer of a third-party GPAI model),
  high-risk by default with a documented Art. 6(3) derogation path, the obligations each
  classification triggers, the application dates and the re-classification triggers (#23).
- `.claude/hooks/sdd-gate.py` — `UserPromptSubmit` hook that blocks `/sdd-plan`, `/sdd-tasks`,
  `/sdd-implement` and `/sdd-taskstoissues` on an unapproved spec and surfaces the checklist
  state; 11 tests in `tests/hooks/`, run by `check-corpus.sh` C11; ADR-0092 → Accepted (#22).
- ADR-0092 (Proposed): spec-kit `before_/after_<command>` hooks mapped to Claude Code hooks —
  `UserPromptSubmit` gate for the code-producing `/sdd-*` commands adopted (to implement),
  `Stop`-based continuation refused (Constitution V) (#20).
- `docs/sdlc/spec-kit-upstream.json` (machine-readable upstream pin, checked by C10),
  `docs/sdlc/spec-kit-sync.md` (quarterly adopt/adapt/refuse procedure) and
  `scripts/bash/spec-kit-diff.sh` (tracked-file diff against upstream via `gh`) (#19).
- `scripts/python/render_commands.py` / `scripts/bash/render-commands.sh`: the `sdd-*` commands
  rendered for Copilot (`.github/skills/`), Cursor (`.cursor/skills/`), Codex (`.agents/skills/`)
  and Gemini CLI (`.gemini/commands/*.toml`); committed copies checked by `check-corpus.sh` C9 (#17).
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

- SPEC-LGS-001 feature spec `approved` by its owner via Spec-as-PR (#21, 2026-09-13); plan
  Constitution Check I → pass; threat-model path corrected to the existing file.
- `AGENTS.md` rewritten for the corpus: a per-agent table of what Claude Code, Copilot, Cursor,
  Codex and Gemini receive (and do not), corpus paths in the do-not-edit list, the `/sdd-*`
  workflow and the real validation commands (#18).
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
