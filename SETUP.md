<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Adopting the corpus

> This repository is a documentation, governance and agent-operating corpus. It ships no
> application code, no `Makefile`, no CI and no service registry. **Adopting** it means copying
> one of the layers below into your product repository and wiring the rest to what that
> repository already has. Every command on this page runs *here*; nothing on it assumes a file
> this corpus does not contain.

## 0. Ten-minute check (in this repository)

```bash
git clone https://github.com/valdomirosouza/Spec-Agentic-SDLC.git && cd Spec-Agentic-SDLC
cat version.txt                                        # 1.1.0
scripts/bash/create-new-feature.sh --json --dry-run "Add cursor pagination to the requests list"
SDD_FEATURE_DIRECTORY=specs/features/SPEC-LGS-001-log-based-golden-signals \
  scripts/bash/check-prerequisites.sh --require-spec --require-plan --require-tasks --include-tasks
python3 .claude/hooks/verify-high-risk-guard.py       # high-risk-action guard self-test
```

Open the repository in Claude Code and run `/sdd-specify <description>`: the feature bundle
appears under `specs/features/<SPEC-ID>-<slug>/`. That is the whole minimal layer working.

## 1. Choose a layer

| Layer        | Copy these paths                                                                                                                                                        | You get                                                                                                   |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **minimal**  | `memory/`, `templates/`, `scripts/bash/` (except `check-corpus.sh`), `.claude/skills/sdd-*/`, `.claude/settings.json`, `.claude/hooks/`, `docs/governance/systems-of-record{,.sample}.yaml`, `docs/sre/slo/schema/run-record.schema.json`, `docs/audit/schema/`, `specs/spec-frontmatter.schema.json`, `specs/features/README.md` | The spec-kit-style workflow (`/sdd-*`), the constitution, the feature bundle, the high-risk-action guard and the systems of record it reads, the batch run record's and IPE evidence's schemas |
| **governed** | minimal + `CLAUDE.md`, `AGENTS.md`, `CLAUDE_SESSION_INIT.md`, `skills/`, `.claude/skills/` (all), `.claude/agents/`, `.claude/personas/`, `docs/adr/`, `docs/process/`, `docs/sdlc/`, `docs/governance/`, `specs/security/`, `harness/`, `.github/` templates | The 15-phase lifecycle with nine human gates, delivery agents, `/deliver`, ADRs, control matrices, PR/issue templates, harness gate specs |
| **full**     | governed + everything else under `docs/` and `specs/` (privacy, compliance, SRE, audit, runbooks, product, GTM)                                                          | The complete compliance and audit evidence corpus (LGPD/GDPR, ISO 27001, SOX, SOC 2, DORA, PRR)           |

`check-corpus.sh` verifies governance, so it arrives with **governed** — the layer that
brings the governance to verify. A `minimal` adoption that ran it got twenty checks over files
it had deliberately declined, and seven failures for them.

Copy with `scripts/bash/adopt.sh --here --layer <minimal|governed|full> [--integration copilot|cursor|gemini|codex]`
(run from a clone of this corpus, or `adopt.sh <target-dir>` from here; ADR-0091). It never
overwrites an existing file without `--force`, never deletes, and runs no git command. Then edit, do not append: `CLAUDE.md` and
`AGENTS.md` are meant to be **merged** with yours, keeping §3 (inviolable rules) and §14
(escalation) intact.

## 2. What your repository provides

The corpus describes controls that are *implemented* in the product repository. These paths and
commands are referenced throughout `docs/`, `specs/`, `skills/` and `CLAUDE.md` and must exist
(or be replaced by your equivalents) before the referenced gate is meaningful:

| Referenced in the corpus                          | You provide                                              | If you do not have it                                                |
| ------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
| `src/`, `tests/`, `services/`, `frontend/`        | your code and tests                                      | —                                                                    |
| `make <target>` (`lint-python`, `test-unit-python`, `doctor`, …) | your `Makefile` or CI equivalents          | map each target named in `CLAUDE.md` §0 to your own command          |
| `services.yaml`                                   | your service/topic registry                              | the `sdd-*` skills skip registry checks; delete the row from `CLAUDE.md` §0.1 |
| `.github/workflows/`                              | your CI (`pr-governance`, `ci.yml`, `cd-*.yml`)          | run `harness/*.yml` gate specs by hand or port them to your CI       |
| `scripts/governance/*.py`                         | deterministic gates (spec registry, control matrices, test integrity) | `/sdd-analyze` is their human-readable twin until you port them |
| `version.txt`, `pyproject.toml`, `CHANGELOG.md`   | your version of record and changelog                     | copy this corpus's `version.txt`/`CHANGELOG.md` pattern             |
| `.env.example`, `.github/CODEOWNERS`              | your secrets template and ownership map                  | `CLAUDE.md` §8 lists the roles CODEOWNERS should encode              |

`CLAUDE_SESSION_INIT.md` carries the same split so every agent session knows which side a path
belongs to, and `docs/reference/adopter-provided-paths.md` is the generated inventory of every
file that names one (each such file carries an `adopter-paths` marker; `check-corpus.sh` C7).

**Declare your shape, and what does not apply (ADR-0098).** In
`docs/governance/applicability-matrix.yml`, set `adoption_profile` to `service` (the default) or
`batch-data`. If a `check-corpus.sh` check cannot apply to your repository, list it under
`not_applicable:` with its exact name, a `reason`, an `owner` and a `review_by` date. Its failure
is then shown as `n/a: <reason>` and is not counted until that date. Do not leave it failing, and
do not stop running it: a permanently red run hides the next real failure. Checks that enforce a
protected Constitution article are refused; C21 lists every declaration on each run.

## 3. Wire the Claude Code layer

1. `.claude/settings.json` registers the `PreToolUse` high-risk-action guard. If you already
   have a `settings.json`, merge the `hooks` block; run
   `python3 .claude/hooks/verify-high-risk-guard.py` afterwards — it asserts the wiring.
2. `/sdd-constitution` — review `memory/constitution.md`. Articles I, II, V, VII and IX are
   protected (strengthen only); rewrite III, IV, VI, VIII for your domain and bump the version.
3. Start a feature: `/sdd-specify …` → Spec-as-PR → `/sdd-plan` → `/sdd-checklist` →
   `/sdd-tasks` → `/sdd-analyze` → `/sdd-implement` ⇄ `/sdd-converge`. Every command names the
   human gate it stops at.
4. For delivery, invoke `asdd-orchestrator` — the delivery entrypoint (ADR-0095). To rehearse a
   spec through the 15 phases with no side effects first, `/deliver dry-run <spec.md>`.

## 4. Keep it in sync

- The corpus version is `version.txt`; changes are in `CHANGELOG.md`. Record the version you
  adopted in your own changelog.
- The spec-kit primitives are pinned to a github/spec-kit commit in
  `docs/sdlc/spec-kit-upstream.json`, the source of record for the pin (`c438494`, v1.3.2, as of
  1.1.0); the adoption decisions are in ADR-0090 and
  `docs/sdlc/spec-kit-comparison.md`, the sync procedure in `docs/sdlc/spec-kit-sync.md`.
- Number your own ADRs from **ADR-1000** (ADR-0097): ADR-0001–0999 belong to the corpus, so a
  sync never collides with yours. Index them in a "Local ADRs (1000+)" table in
  `docs/adr/README.md`. A local ADR that already collides is restated as ADR-1NNN, and the old file
  is marked `Superseded by ADR-1NNN`, never renamed.
- Copilot, Cursor, Codex and Gemini CLI receive the rendered `sdd-*` commands (`--integration`,
  ADR-0091); `AGENTS.md` §1 says what each agent does and does not get.

## 5. Where things are

| Need                                   | Path                                                       |
| -------------------------------------- | ---------------------------------------------------------- |
| Root of authority                      | `memory/constitution.md`                                   |
| Operating contract for agents          | `CLAUDE.md` (deep), `AGENTS.md` (cross-tool), `CLAUDE_SESSION_INIT.md` (primer) |
| Workflow commands                      | `.claude/skills/sdd-*/SKILL.md`, `.claude/skills/README.md` |
| Feature bundle layout and example      | `specs/features/README.md`, `specs/features/SPEC-LGS-001-log-based-golden-signals/` |
| 15-phase lifecycle                     | `docs/process/WORKFLOW.md`, `docs/sdlc/agentic-spec-driven-delivery.md` |
| Customising or removing extensions     | `CUSTOMISING.md` (written for the product template; paths there are adopter-side) |
| Original product-template setup        | `docs/reference/repository-template-v2-SETUP.md` (archived) |
