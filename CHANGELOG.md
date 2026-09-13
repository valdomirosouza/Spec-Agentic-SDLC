<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Changelog

All notable changes to the Spec-Agentic-SDLC corpus are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the version of record is
`version.txt` (ADR-0057) and follows SemVer. Governance-relevant changes cite the ADR that
authorises them.

## [Unreleased]

### Added

- `tests/scripts/test_check_corpus.py` — the mutation harness: every entry injects the defect a
  check exists to catch and requires **that** check to fail, named. Fifty assertions had never been
  exercised, which is why three vacuous checks survived one round and two more the next (#66).
- `scripts/python/mutation_coverage.py` and `tests/.mutation-coverage-baseline.json` — a ratchet on
  how much of the verifier is proved able to fail (15 of 49 today). Deleting a proof lowers the
  count; adding a check without a proof leaves the count alone and lowers the ratio, which is the
  case a count cannot see (#75).
- `.github/workflows/corpus-measure.yml` — the weekly measurement. A level is earned by repetition
  and the monthly cadence existed only as a sentence, with no trigger anywhere in the repository
  (#72). Rewritten one round later: it compared against a baseline the commit gate pins, measured
  without a token so the archived report lost its CI rows, and never returned the report, so a
  second data point could not exist (#74).
- `tests/scripts/test_corpus_measure_workflow.py` — eight assertions on the scheduled job, the
  substitute for being able to run it: token scope, ordering, the delta file written and read under
  one variable, the pull request that forms the series, and the verbs Constitution V forbids (#74).
- The coverage ratchet records the check **names**, not only the counts. Guarding the ratio alone
  inverted the incentive: a ratio rises when its denominator shrinks, so deleting twenty unproved
  checks moved coverage from 32% to 52% and the gate approved it (#79).
- `scripts/python/check_open_items.py` — every open item now carries an ISO date, which fails once
  it passes, or a declared `on-event: <trigger>`. All 31 were prose deferrals to a review nothing
  convenes, so none could ever come due; 11 became the next quarterly date and 19 a named trigger
  (#78).
- `scripts/python/check_changelog.py` — a change to scripts, workflows, hooks or the normative
  contract now owes a changelog entry, with a declared `CHANGELOG_WAIVER` as the only way past
  (#77).
- `asdd_state.py migrate` — converts a v1 state to v2 by walking the handoffs, recovering artefacts
  the old basename map had lost (#76).
- `corpus_metrics.py --drift` — the periodic comparison, against a baseline at least seven days old
  and including the numbers that move without anyone editing a file (#70, #73).

- `LICENSE` (MIT), `CITATION.cff` and a README license section (#2).
- `version.txt` (1.0.0) and this changelog (#3).
- `skills/engineering/change-discipline.md` — the Karpathy guidelines wired into the skill system
  as a corpus skill, with the two principles the constitution already binds kept as pointers and
  **Surgical Changes** adopted as the rule the corpus lacked; PR checklist and the 10-step workflow
  gain the scope item (#64, #65).
- The "160x faster" claim (withdrawn — see below) and the `/deliver` instruction that generated it removed;
  the metrics report gains a Productivity section with the measured side only and the four things
  a legitimate ratio would require; a C8 invariant blocks an unqualified delivery-throughput ratio
  from returning (#55).
- First monitoring cycle executed, `docs/sre/monitoring/2026-09-13-first-cycle.md`; the plan gains
  a fifth signal family (corpus integrity) because in a repository with no runtime the other four
  are unobservable and four empty rows are not a monitoring plan (#54).
- `scripts/python/check_data_quality.py` — 14 executable rules across all six dimensions over the
  corpus's own datasets (spec registry, ADR index, control matrices, adopter-path inventory), with
  11 tests, wired as C15: critical blocks, major is reported on every run (#53).
- `scripts/python/corpus_metrics.py` with 9 tests and the first measurement the corpus has taken
  of itself, `docs/sre/corpus-metrics-2026-09-13.md`: 59 commits over 2 active days, 9.3% CI
  failure rate, 23.2:1 prose-to-code. Every number names its method and §4 lists the five metrics
  this repository cannot produce, with the reason (#52).
- First red-team exercise executed (RT-2026-09-13, #51): 12 attempts against the two live hooks
  and `vcs.sh`. Found and fixed **RT-04 (High)** — `$(which git) push` evaded the high-risk guard
  because command substitution hid the binary name from the pattern; the guard now normalises that
  indirection. All 12 attempts retained as tests and run by `check-corpus.sh`.
- Three authority conflicts resolved and pinned as invariants: the arbiter for phase-gate data
  (#48), the distinction between 13 blocking and 9 human gates (#49), and one coverage floor
  declared in ADR-0022 and referenced rather than restated (#50).
- `scripts/python/build_spec_registry.py` with 10 tests, wired as `check-corpus.sh` C13 — the spec
  registry had drifted to 50 of 58 entries because its generator lived in the product repository
  and no check compared it to disk; it is now regenerated here and byte-compared on every push (#47).
- `scripts/python/asdd_state.py` and `scripts/bash/vcs.sh` — the two scripts the 16 delivery agents
  call and that did not exist; 12 + 13 tests, two new C8 invariants (#44, #45).
- ADR-0095 — one delivery entrypoint, and the single named version-control exception agents may
  take (a local feature branch, behind a guard) (#46).
- `scripts/python/check_control_matrix.py` with 14 tests, wired as `check-corpus.sh` C12 — the
  validator several documents cited and that did not exist here. Its first run found 83 defects,
  all fixed: 75 adopter-provided paths in the two OWASP matrices now carry the `adopter:` prefix
  the header promised, seven partial controls gained a gap statement, and one broken evidence path
  in the EU AI Act matrix was corrected (#43).
- `docs/ai-governance/model-registry.md` — the governance layer around the dependency manifest:
  model states with a recorded refusal, a ten-row AI component inventory including prompts and the
  embedding model, the promotion record, and the three GPAI provenance items a deployer must retain
  and has not (#42).
- `specs/ai/red-team-program.md` — ten techniques mapped to OWASP LLM ids, rules of engagement,
  five cadence triggers including a blocking exercise before any autonomy increase, and every
  Critical/High/Medium finding required to become an abuse case; the exercise log records the
  empty state deliberately (#41).
- `docs/runbooks/RB-AI-001-ai-incident.md` — five AI incident scenarios (jailbreak, harmful
  output, hallucination reaching a decision, unapproved irreversible action, model behaviour
  change), four containment levers ordered by blast radius, an evidence-preservation table and
  eight recovery criteria (#40).
- `docs/ai-governance/dual-use-registry.md` populated with the seven always-HITL action categories,
  each assessed against D-01 to D-06 with its mitigation, plus the entry rule that an unregistered
  action type is not activatable (#39).
- `templates/model-card-template.md` (the former blank card, moved) and two filled artefacts:
  `docs/ai-governance/model-card.md` for the pinned model and `docs/ai-governance/system-card.md`
  describing the system the model sits inside, including what it cannot do by construction and a
  residual-risk table that does not claim zero (#38).
- `docs/privacy/sub-processor-register.md` — six rows with the personal data each can access, its
  class, processing region, transfer instrument, contract and assessment state (all `pending`, the
  true state), the seven-step addition path and a retirement rule that keeps the row (#37).
- ADR-0094 — data residency per data class (L1 never leaves the primary region), the rule that a
  prompt is a transfer and a model's processing region is a governed fact, sovereignty separated
  from residency, and backups, logs and telemetry following the data; answers the three open
  questions in the control-applicability matrix (#36).
- `specs/privacy/test-data-management.md` — no production copy into lower environments, environment
  classification, synthetic-first provisioning, the five masking techniques with their failure
  modes, the verify-after-load step, and the two agent-specific cases (prompts and traces are test
  data; agent memory must not be seeded from production) (#35).
- `specs/privacy/training-data-governance.md` — training as a purpose needing its own basis, the
  lawful-basis table with special-category data prohibited outright, permitted and refused sources,
  and an honest three-part answer on erasure: source and derived datasets erased, no future use,
  and disclosure where a deployed model already carries the value (#34).
- `templates/datasheet-template.md` (Datasheets for Datasets extended with licence, lawful basis
  and mandatory exclusion criteria) and the first instance,
  `docs/data/datasheets/agent-memory-documents.md`, published as `draft` with six unresolved rows
  so the dataset is explicitly not cleared for model use (#33).
- `specs/data/data-lineage.md` — the forward (impact) and backward (provenance) questions, dataset
  granularity with field level for L1/L2 only, the `classification_effect` of each transform,
  three capture points with trace reconciliation, the data-subject-request walk, and decay
  controls (#32).
- `docs/data/business-glossary.md` (business meaning, separate from the technical glossary, with a
  "not to be confused with" field on every term) and `docs/data/data-catalog.md` (governance index:
  owner, steward, custodian, classification, contract, quality, model use) (#31).
- `specs/data/data-contracts.md` and `templates/data-contract-template.md` — the contract around
  the schema (parties, semantics, classification, quality, service level, lifecycle, lineage), the
  five-step breaking-change process with a minimum coexistence window, and the rule that an agent
  reading a dataset is a consumer (#30).
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

### Fixed

- **Vacuous checks, second and third pass.** The refusal check counted occurrences of a string and
  stayed green with every refusal neutralised to a no-op; the productivity-ratio regex had lost the
  forms it used to catch; the coverage-floor regex exempted any line citing the ADR, which is what a
  restated number would do; the scope-discipline check named two placements and verified neither
  (#67, #68). Each is now proved by mutation.
- **The evidence rule had been widened until it exempted the case that created it** — 145 of 146
  paths exempt by directory prefix, including `tests/` and `.github/workflows/`, which exist here.
  Exemption is now an explicit `adopter:` / `ci:` / `planned:` marker, and severity follows the
  claim a spec makes about itself (#69).
- **The freshness check approved a report it could prove was stale**, comparing section headings and
  no numbers (#70).
- **The periodic comparison could not find anything, by construction.** It read the newest report,
  which the commit gate forces to equal the live numbers, so it measured a number against itself and
  answered "no movement" even at a threshold of 0.0001% (#73).
- **The delivery state's order guard had a one-entry escape** (a forced entry became the yardstick),
  one flag cleared two guards, and `--json` skipped validation entirely — the output a governance
  gate consumes (#71).
- Seven commits of round 5, including a breaking schema change, reached `main` with no changelog
  entry at all; nothing in this corpus checked (#77).

### Changed

- **BREAKING (adopters): delivery state schema `asdd_state_v1` to `asdd_state_v2`.** The
  `artifacts` map changed meaning from `{basename: path}` to `{path: phase}`. Both shapes are
  objects of strings, so a v1 file loaded as v2 renders every artefact inverted and validates
  clean. A v1 file is now refused with an explanation. **Convert with
  `asdd_state.py migrate --feature <ID>`** — it keeps every handoff. The first version of that
  message said to re-run `init --force`, which destroys the handoff trail Article VII reads
  (#71, #76).
- `append-handoff` takes `--force-order` and `--force-unblock` in place of a single `--force`
  (#71).
- The drift threshold is 1%, chosen by computing what each row can see and publishing that table in
  the report; at the previous 2% a newly added ADR was invisible (#73).

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
