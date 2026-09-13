<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Tasks: [FEATURE NAME]

**Input**: `specs/features/[SPEC-ID]-[slug]/` — plan.md (required), spec.md (required), research.md, data-model.md, contracts/
**Phase**: 6 — Development (ADR-0058) | **Branch**: `feature/[SPEC-ID]-[slug]`

<!--
  Produced by /sdd-tasks. Adopted from spec-kit's tasks-template: Setup → Foundational → one
  phase per user story (priority order) → Polish; [P] marks tasks that can run in parallel.
  Extended with this repository's rules: tests are NOT optional (Constitution II), every task
  cites the requirement it serves, and each task declares ≤ 2 skills (ADR-0060).
-->

## Format: `- [ ] [ID] [P?] [Story] Description with exact file path — Refs: FR/AC`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1, US2 … (required on user-story phases only)
- **Refs**: the FR-/AC-/NFR- ids the task satisfies (traceability, Constitution VII)
- **Skills**: at most two `skills/…` files per task; a third means the task must be split

## Phase 1: Setup (shared infrastructure)

- [ ] T001 Create feature branch `feature/[SPEC-ID]-[slug]` and confirm spec status is `approved`
- [ ] T002 [P] Register new topics/services in `services.yaml` + AsyncAPI if the plan adds any

## Phase 2: Foundational (blocking prerequisites)

**⚠️ No user-story work starts until this phase is complete.**

- [ ] T003 Data model / migration skeleton per data-model.md (`alembic/versions/…`) — Refs: FR-0x
- [ ] T004 [P] Contract stubs from contracts/ (OpenAPI/AsyncAPI deltas committed) — Refs: FR-0x

**Checkpoint**: foundation ready; stories may proceed in parallel.

## Phase 3: User Story 1 — [Title] (Priority: P1) 🎯 MVP

**Goal**: [what this story delivers]
**Independent Test**: [how to verify it alone]
**Skills**: `skills/…`, `skills/…`

### Tests first (write, run, watch them FAIL)

- [ ] T010 [P] [US1] Contract test in `tests/contract/test_[name].py` — Refs: AC-01
- [ ] T011 [P] [US1] Unit tests in `tests/unit/[path]/test_[name].py` with `requirement("SPEC-…/FR-01")` — Refs: FR-01

### Implementation

- [ ] T012 [P] [US1] Entity/model in `src/[path]` — Refs: FR-01
- [ ] T013 [US1] Service in `src/[path]` (depends on T012) — Refs: FR-01, FR-02
- [ ] T014 [US1] Endpoint/consumer in `src/[path]` + OpenAPI/AsyncAPI updated — Refs: AC-01
- [ ] T015 [US1] Guardrails at the boundary (pii_filter / prompt_injection_guard / output_sanitizer) — Refs: NFR-0x
- [ ] T016 [US1] Metrics/spans per plan Observability Design — Refs: NFR-0x

**Checkpoint**: US1 fully functional and independently testable.

## Phase 4: User Story 2 — [Title] (Priority: P2)

[same structure]

## Phase N: Polish & Cross-Cutting

- [ ] TXXX [P] Runbook / dashboard updates per plan — Refs: NFR-0x
- [ ] TXXX Abuse-case tests if `src/agents/` or `src/guardrails/` were touched (count must not drop)
- [ ] TXXX Spec frontmatter: fill `implemented_by`, `verified_by`; status → `implemented` at merge
- [ ] TXXX Run quickstart.md validation end to end

## Dependencies & Execution Order

- Setup → Foundational (blocks all stories) → stories in priority order (or in parallel) → Polish
- Within a story: tests → models → services → endpoints → integration
- Tasks touching the same file run sequentially

## Implementation Strategy

1. **MVP first**: Setup + Foundational + User Story 1 → STOP, validate, demo.
2. **Incremental**: add one story at a time; each adds value without breaking previous stories.
3. **Scope per run**: for large features, run `/sdd-implement` per phase or per story to stay
   inside the context window (see docs/sdlc/spec-kit-comparison.md, "complex features").

## Human gates touched by these tasks

- [ ] Code review approval (Phase 7) — required before merge
- [ ] Security approval if any HIGH/CRITICAL finding (Phase 9)
- [ ] AI governance approval if agents/guardrails/autonomy touched (Phase 10)
