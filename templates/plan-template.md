<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Implementation Plan: [FEATURE]

**Spec**: `specs/features/[SPEC-ID]-[slug]/spec.md` | **Branch**: `feature/[SPEC-ID]-[slug]` | **Date**: [DATE]
**Phase**: 5 — Architecture & Technical Design (ADR-0058) | **Risk class**: [from spec]

<!--
  Produced by /sdd-plan. This is where the HOW lives: stack, architecture, data model, contracts.
  Keep it readable; long algorithms and code samples go to research.md or contracts/.
  Adopted from spec-kit's plan-template and extended with this repository's Phase 5 obligations
  (ADR, threat model, DPIA, observability design).
-->

## Summary

[Primary requirement + technical approach, two or three sentences]

## Technical Context

**Language/Version**: [e.g. Python 3.13 — or NEEDS CLARIFICATION]
**Primary Dependencies**: [e.g. FastAPI, asyncpg — or NEEDS CLARIFICATION]
**Storage**: [PostgreSQL / Redis / N/A]
**Messaging**: [Kafka topic(s) — must exist in services.yaml + AsyncAPI, or N/A]
**Testing**: [pytest markers, contract tests, abuse cases]
**Target Platform**: [K8s service / worker / job / frontend]
**Performance Goals**: [e.g. p95 < 300 ms at 200 rps]
**Constraints**: [e.g. no new PII, offline-capable]
**Scale/Scope**: [e.g. 10k requests/day]

## Constitution Check

_GATE: must pass before Phase 0 research; re-checked after Phase 1 design. Cite the article._

| Article               | Question the plan must answer                                        | Status (pass / justified / FAIL) |
| --------------------- | -------------------------------------------------------------------- | -------------------------------- |
| I Specification First | Is the spec `approved`? Does every plan decision trace to an FR/NFR? |                                  |
| II Test-Backed Change | Which tests fail first? Which coverage floors apply?                 |                                  |
| III Privacy by Design | New PII? Class? Masking point? DPIA needed?                          |                                  |
| IV Security Gates     | New attack surface? STRIDE pass done? Controls in the matrices?      |                                  |
| V Human Oversight     | New agent action types? Autonomy level? HITL route?                  |                                  |
| VI Observability      | Golden Signals, SLO, runbook, rollback indicator defined?            |                                  |
| VII Traceability      | Spec id, ADR id(s), issue number present on every artefact?          |                                  |
| VIII Simplicity       | Any abstraction/project beyond what the spec needs? (see below)      |                                  |
| IX Grounding          | Every API/config claim verified? Unknowns marked?                    |                                  |

## Phase 5 Obligations (this repository)

- **ADR required?** yes → `docs/adr/ADR-NNNN-<slug>.md` (Draft → Accepted before Phase 6) / no — reason
- **Threat model delta?** yes → `specs/security/threat-model-[SPEC-ID].md` / no — reason
- **DPIA / RIPD?** yes → `docs/privacy/dpia/` / no — reason
- **Phase 10 (AI Safety) mandatory?** yes (touches agents/guardrails/autonomy) / no

## Project Structure

### Documentation (this feature)

```text
specs/features/[SPEC-ID]-[slug]/
├── spec.md              # Phase 4 output (/sdd-specify, /sdd-clarify)
├── plan.md              # This file (/sdd-plan)
├── research.md          # Phase 0 output — decisions, rationale, alternatives
├── data-model.md        # Phase 1 output — entities, fields, state transitions
├── contracts/           # Phase 1 output — OpenAPI/AsyncAPI/Avro deltas
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── checklists/          # requirements.md (built-in) + reviewer checklists
└── tasks.md             # /sdd-tasks output — NOT created by /sdd-plan
```

### Source Code

```text
# Replace with the concrete layout for this feature; delete unused branches.
src/<layer>/...
tests/unit/... tests/integration/... tests/contract/... tests/abuse_cases/...
```

**Structure Decision**: [which directories, and why]

## Phase 0 — Outline & Research → `research.md`

For each NEEDS CLARIFICATION in Technical Context, each dependency and each integration:

- **Decision**: [what was chosen]
- **Rationale**: [why]
- **Alternatives considered**: [what else was evaluated]

## Phase 1 — Design & Contracts → `data-model.md`, `contracts/`, `quickstart.md`

1. Entities, fields, validation rules and state transitions from the spec → `data-model.md`
2. Interface contracts: REST (OpenAPI delta), events (AsyncAPI + Avro delta), CLI → `contracts/`
3. Runnable validation scenarios proving the feature end to end → `quickstart.md`
4. Re-run the Constitution Check.

## Observability Design (Article VI)

| Item                | Value                         |
| ------------------- | ----------------------------- |
| CUJ impacted        |                               |
| New metrics / spans |                               |
| SLO entry           | `docs/sre/slo/<service>.yaml` |
| Dashboard / runbook |                               |
| Rollback indicator  |                               |

## Complexity Tracking

> Fill ONLY if the Constitution Check has "justified" rows.

| Violation | Why needed | Simpler alternative rejected because |
| --------- | ---------- | ------------------------------------ |
|           |            |                                      |
