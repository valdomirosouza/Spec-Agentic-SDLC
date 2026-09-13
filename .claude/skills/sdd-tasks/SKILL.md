---
name: sdd-tasks
description: Generate the dependency-ordered tasks.md for the active feature from plan.md and spec.md — Setup, Foundational, one phase per user story in priority order, Polish — with [P] parallel markers, exact file paths, FR/AC references and tests-first ordering. Trigger on "tasks", "break down the plan", "task list". Usage — /sdd-tasks [scope or emphasis].
---

# /sdd-tasks — design artefacts → executable task list

Adapted from spec-kit `/speckit.tasks`. Differences from spec-kit: tests are **mandatory**
(Constitution II), every task carries `Refs:` to the FR/AC/NFR it serves (Constitution VII),
and every task declares ≤ 2 skills (ADR-0060) — a third means split.

## User input

```text
$ARGUMENTS
```

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec --require-plan --require-approved`
   → `FEATURE_DIR`, `AVAILABLE_DOCS`. Load `memory/constitution.md`.
2. **Load**: plan.md (stack, structure, Phase 5 decisions), spec.md (stories with priorities,
   FR/AC tables, §7 governance, §8 Golden Signals); if present data-model.md, contracts/,
   research.md, quickstart.md; the roadmap entry if the spec is a slice.
3. **Derive tasks** into `FEATURE_DIR/tasks.md` from `templates/tasks-template.md`:
   - Phase 1 Setup · Phase 2 Foundational (blocking) · Phase 3+ one phase per user story
     (P1 = MVP) · final Polish.
   - Within a story: tests first (contract → integration → unit, with `requirement()` markers,
     written to FAIL) → models → services → endpoints/consumers → guardrails at boundaries →
     metrics/spans → integration.
   - Entities → the earliest story that needs them; contracts → the story they serve; field
     constraints quoted verbatim from data-model.md.
   - Governance tasks the spec §7 implies: PII masking, DPIA artefact, abuse-case tests when
     `src/agents/` or `src/guardrails/` are touched, threat-model update, runbook/dashboard.
   - Format (strict): `- [ ] T001 [P] [US1] Description in path/to/file — Refs: FR-01, AC-01`.
   - `[P]` only for different files with no dependency on an incomplete task.
4. **Dependencies & strategy** sections: story order, parallel opportunities, MVP-first plan,
   and the per-run scoping advice for large features (run per phase/story).
5. **Human gates** listed at the end (code review, security approval, AI governance).
6. Validate: every story independently testable; every FR has ≥ 1 task; every task has an id,
   path and Refs.

## Completion report

Path, total tasks, tasks per story, parallel count, MVP scope (usually US1), format check.

## Done when

- [ ] tasks.md written in the strict format with phases, Refs and gates
- [ ] Every FR/AC covered by ≥ 1 task; tests precede implementation in every story
