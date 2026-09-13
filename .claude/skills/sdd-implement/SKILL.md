---
name: sdd-implement
description: Execute tasks.md for the active feature (Phase 6 — Development) phase by phase, tests first, marking tasks [X], respecting [P] markers, checklist gates and every human gate of ADR-0058; scope a run to a phase, a story or a task range to stay inside the context window. Trigger on "implement", "execute the tasks", "build the feature". Usage — /sdd-implement [only phase N | only US1 | T001-T010 | delegate [P] tasks to sub-agents].
---

# /sdd-implement — execute the task list

Adapted from spec-kit `/speckit.implement`. In this repository implementation is Phase 6 of
ADR-0058 and is bound by CLAUDE.md §2 (10-step workflow), §3 (inviolable rules) and §14
(escalation). Agents implement; humans review, merge, deploy.

## User input

```text
$ARGUMENTS
```

Scoping is expected for anything non-trivial: `only the Setup and Foundational phases`,
`only User Story 1`, `T010-T017`, `delegate each [P] task to a sub-agent`. Completed tasks are
`[X]`, so the next run resumes where this one stopped.

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec --require-plan --require-tasks --require-approved --include-tasks`.
   A spec that is not `approved` stops the command (Constitution I).
2. **Checklist gate**: for every file in `FEATURE_DIR/checklists/`, count checked/unchecked and
   print the table. Unchecked items → STOP and ask "proceed anyway?"; never modify markers.
3. **Load** tasks.md, plan.md, data-model.md, contracts/, research.md, quickstart.md,
   `memory/constitution.md`, and the ≤ 2 skills each task declares (a task that needs a third
   is split first — ADR-0060).
4. **Session bootstrap** (CLAUDE.md §2): `CLAUDE_SESSION_INIT.md`, the adopting repository's
   service registry (`services.yaml`) when it exists, the spec,
   the GitHub issue; confirm the branch is `feature/<SPEC-ID>-<slug>`.
5. **Execute** phase by phase, in order; `[P]` tasks may run together (different files);
   same-file tasks sequentially. Within a story: tests first and **watch them fail**, then
   models → services → endpoints → guardrails → observability. Mark each finished task `[X]`
   immediately. Halt on a failing non-parallel task; report failed `[P]` tasks and continue
   with the rest.
6. **Hard stops** (`[HITL-ESCALATE]`, CLAUDE.md §14.1): touching the adopting repository's
   `src/guardrails/` or the HITL
   gateway · any feature-flag change · > 3 ADRs · coverage would drop below 75% · a spec
   reference cannot be found · a requirement contradicts an ADR or another approved spec.
7. **Never**: bypass a gate (`--no-verify`), weaken or delete a test, reduce the abuse-case
   count, commit a secret or real PII, invent an API (Constitution IV, II, III, IX).
8. **Per task** commit with the conventional message and trailer
   `Refs: #<issue>, <SPEC-ID>, ADR-NNNN` (CLAUDE.md §6). Record any divergence from the spec
   as a `SPEC_DEVIATION` marker with reason and reference (skills/sdlc/spec-lifecycle.md).
9. **Completion validation**: the adopting repository's lint/type/test gates green (its
   `make` targets or CI equivalents — none exist in this corpus); coverage ≥ floors; spec frontmatter
   `implemented_by` / `verified_by` filled; quickstart.md scenarios pass.

## Completion report

Tasks completed/remaining, tests run and their result (verbatim failures if any), gates run,
escalations raised, `SPEC_DEVIATION`s recorded, next command (`/sdd-converge`, then the PR for
Phase 7 human review).

## Done when

- [ ] Every task in scope `[X]`; tests written before code and now passing
- [ ] No gate bypassed; no protected path touched without escalation
- [ ] Traceability trailers on every commit
