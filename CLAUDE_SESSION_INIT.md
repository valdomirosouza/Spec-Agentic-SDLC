<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Claude Code Session Primer

> Auto-loaded at session start. Supplements `CLAUDE.md` and `skills/sdlc/agent-onboarding.md`.
> Keep this file concise — it is loaded into every session's context window.

---

## Repo Identity

- **Repo:** Spec-Agentic-SDLC — https://github.com/valdomirosouza/Spec-Agentic-SDLC
- **Type:** Documentation, governance and agent-operating **corpus**. No application code.
  Meant to be copied into, or referenced from, a product repository (see `SETUP.md`).
- **Current version:** `version.txt` (1.0.0) · changes in `CHANGELOG.md`
- **Root of authority:** `memory/constitution.md` (nine articles) → `CLAUDE.md` (operating contract)
- **Branch convention:** `main` only; feature work on `feature/SPEC-<DOMAIN>-NNN-<slug>` (ADR-0085)
- **Provenance:** Repository-Template-v2 (Waves 11–15) + github/spec-kit primitives (ADR-0090,
  upstream pinned at `d848fb4`, v1.0.6)

## What exists here vs. what the adopting repository provides

| Provided by this corpus                                           | Provided by the adopting product repository                |
| ----------------------------------------------------------------- | ---------------------------------------------------------- |
| `memory/`, `templates/`, `scripts/bash/`, `.claude/`, `harness/`  | `src/`, `tests/`, `Makefile` / `make` targets              |
| `specs/`, `docs/` (ADRs, process, SRE, privacy, compliance, audit) | `services.yaml`, `.github/workflows/`, `scripts/governance/` |
| `skills/` (plain-Markdown skills), `prompts/`                     | `pyproject.toml`, `.env.example`, CODEOWNERS               |

Any document that names a path from the right-hand column describes the adopting repository.
Do not create those files here; do not treat their absence as a defect.

## Critical Paths (highest sensitivity — escalate before touching)

| Path                                 | Why sensitive                                                    |
| ------------------------------------ | ---------------------------------------------------------------- |
| `memory/constitution.md`             | Root of authority; protected articles I, II, V, VII, IX          |
| `.claude/hooks/`, `.claude/settings.json` | High-risk-action guard (never push/merge/release/deploy) and the sdd-gate (no code-producing `/sdd-*` command on an unapproved spec) |
| `.claude/skills/sdd-*/`              | The `/sdd-*` workflow; changes must stay consistent with ADR-0090 |
| `templates/`, `scripts/bash/`        | Executable templates and helpers every feature bundle depends on |
| `docs/adr/`                          | Binding decisions; numbering must stay contiguous                |
| `specs/security/*.yaml`              | Authoritative OWASP control matrices (ADR-0072)                  |

## Open Work

```bash
gh issue list --repo valdomirosouza/Spec-Agentic-SDLC --state open
```

Improvement plan (spec-kit comparison, 2026-09-12): `wave-0` Foundations → `wave-1`
Demonstrable flow → `wave-2` Verified corpus → `wave-3` Portable and syncable.

## The /sdd-* workflow (ADR-0090)

```text
/sdd-constitution → /sdd-specify → /sdd-clarify → [Spec-as-PR approval] → /sdd-plan
  → /sdd-checklist → /sdd-tasks → /sdd-analyze → /sdd-implement ⇄ /sdd-converge → PR (Phase 7)
```

Helper scripts: `scripts/bash/create-new-feature.sh --json "<description>"`,
`check-prerequisites.sh --json [--require-approved]`, `setup-plan.sh --json`. Active feature
is resolved from `SDD_FEATURE_DIRECTORY`, `.sdd/feature.json` or the branch name.

## Task Atomicity Kickoff (ADR-0060, CLAUDE.md §4)

> Decompose this work so that **no task needs more than 2 repo skills** to finish.
> Treat the 2-skill budget as the _test_ for whether a task is atomic: if a task would
> need a 3rd skill, **split it at that boundary** instead of loading the skill. Each task
> produces **exactly one reviewable artifact** and declares its ≤ 2 bindings under
> `## Skills — load before executing`. `CLAUDE.md` and repo context do **not** count toward
> the budget. Before closing each Agentic SDLC phase, list the artifacts the phase owes and
> create a dedicated atomic task for any that is missing. Run the cross-cutting control
> triggers (`docs/governance/control-applicability-matrix.md`) before every task.

## Session Bootstrap Checklist

- [ ] `memory/constitution.md` read; `CLAUDE.md` §14 escalation triggers noted
- [ ] Work decomposed so each task needs ≤ 2 skills and yields one artifact (ADR-0060)
- [ ] Relevant skill(s) loaded (max 2)
- [ ] Cross-cutting control triggers checked (control-applicability-matrix)
- [ ] GitHub Issue identified with spec reference
- [ ] Spec status confirmed as `approved` before any code-generating step
- [ ] _(adopting repository only)_ `services.yaml` scanned for the affected service

## ADR Quick Index (most recent)

<!-- The highest ADR here must be the highest ADR on disk. Regenerate: the last 20 rows of docs/adr/README.md. -->

| ADR      | Decision                                          |
| -------- | ------------------------------------------------- |
| ADR-0074 | Automated dependency & digest update policy (Reno… |
| ADR-0075 | Resilience fallback policy (degrade-open vs fail-… |
| ADR-0076 | Structured API error model (problem+json flavour)… |
| ADR-0077 | Idempotency keys for write endpoints (Idempotency… |
| ADR-0078 | List-endpoint pagination standard (offset/limit +… |
| ADR-0079 | Prompt externalisation (evaluator + orchestrator … |
| ADR-0080 | Groundedness scoring as an SLI (model-contract te… |
| ADR-0081 | RAG reference pipeline (chunk→embed→retrieve→rera… |
| ADR-0082 | Consolidated backup RPO/RTO + scheduled, evidence… |
| ADR-0083 | Rename `frontend/frontend` → `frontend/web` (refi… |
| ADR-0084 | Dependency & digest updates via Dependabot (super… |
| ADR-0085 | Unified spec identifier (SPEC-<DOMAIN>-NNN) and f… |
| ADR-0086 | HITL approval resumption (ApprovalConsumer execut… |
| ADR-0087 | Marker-based three-way template sync (.template-v… |
| ADR-0088 | Provider-neutral Terraform layering (partial back… |
| ADR-0089 | Documented-capability reachability as a tested in… |
| ADR-0090 | Adopt spec-kit workflow primitives (constitution,… |
| ADR-0091 | Corpus adoption via adopt.sh and rendered per-age… |
| ADR-0092 | spec-kit before/after hooks vs Claude Code hooks … |
| ADR-0093 | EU AI Act role and risk classification (provider …|

Full index: `docs/adr/README.md`

## Process Quick Reference (ADR-0052)

| Document                   | Path                                        | Use when                               |
| -------------------------- | ------------------------------------------- | -------------------------------------- |
| Delivery model (canonical) | `docs/sdlc/agentic-spec-driven-delivery.md` | Understand the workflow + positioning  |
| spec-kit comparison        | `docs/sdlc/spec-kit-comparison.md`          | Why a `/sdd-*` command works as it does |
| Phase lifecycle            | `docs/process/WORKFLOW.md`                  | Any feature task — check current phase |
| HITL governance            | `docs/process/HITL-GOVERNANCE.md`           | Creating discovery/spec artefacts      |
| Definition of Ready        | `docs/process/DEFINITION_OF_READY.md`       | Grooming ceremony / sprint entry       |
| Definition of Done         | `docs/process/DEFINITION_OF_DONE.md`        | PR checklist                           |
| Definition of Release      | `docs/process/DEFINITION_OF_RELEASE.md`     | Release candidate review               |
| RACI matrix                | `docs/process/RACI.md`                      | Unclear ownership question             |
| Sprint tracking            | `docs/process/SPRINT-TRACKING.md`           | Projects board, label taxonomy         |
| Retrospective guide        | `docs/process/RETROSPECTIVE-GUIDE.md`       | Sprint or release retrospective        |
