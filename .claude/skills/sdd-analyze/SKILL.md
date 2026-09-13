---
name: sdd-analyze
description: Read-only cross-artifact consistency analysis of spec.md, plan.md and tasks.md (plus constitution, ADRs and control matrices) before implementation — duplication, ambiguity, underspecification, constitution/ADR conflicts, coverage gaps, terminology drift — reported with severities and a coverage table. Never edits files. Trigger on "analyze", "consistency check", "are spec plan and tasks aligned". Usage — /sdd-analyze.
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->
# /sdd-analyze — cross-artifact consistency gate

Adapted from spec-kit `/speckit.analyze`. This is the human-readable twin of the repository's
deterministic gates (`build_spec_registry.py` S1–S7, `check_open_questions.py`,
`check_doc_references.py`, `check_control_matrix.py` in the source template).

## Operating constraints

- **STRICTLY READ-ONLY.** Output a report; offer remediations; apply nothing.
- **Constitution and ADRs are non-negotiable.** A conflict with a MUST or with an accepted ADR
  is CRITICAL and is fixed in the spec/plan/tasks, never by reinterpreting the principle.

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec --require-plan --require-tasks --include-tasks`.
   Load `memory/constitution.md`; governing ADRs from the spec frontmatter; the control
   matrices `specs/security/*.yaml` if §7 names controls.
2. **Load minimally**: spec (FR/SC/AC tables, stories, edge cases, §7, §8, §12, §13) · plan
   (Technical Context, Constitution Check, Phase 5 decisions, structure) · tasks (ids, phases,
   `[P]`, paths, Refs).
3. **Semantic models**: requirement inventory keyed by FR-/SC-/AC- ids (buildable SCs only);
   story inventory; task → requirement mapping from `Refs:` (fallback: keywords); constitution
   MUST/SHOULD set; ADR decisions that bind the plan.
4. **Detection passes** (≤ 50 findings, overflow summarised):
   A duplication · B ambiguity (vague adjectives, TODO/placeholder, leftover
   `[NEEDS CLARIFICATION]`) · C underspecification (FR without object/outcome, story without
   AC, task path not in plan structure) · D constitution & ADR alignment (incl. missing DPIA
   decision, missing Golden Signals, missing threat-model delta, Phase 10 not planned for
   agent changes) · E coverage (FR with zero tasks; task with no Refs; AC without a named
   test; §10 footer K > 0) · F inconsistency (terminology vs glossary; entities in plan absent
   from spec; task order contradictions; topic in plan not in the adopting
   repository's service registry — `services.yaml`, checked only when that file exists).
5. **Severity**: CRITICAL (constitution/ADR MUST violated, missing core artefact, P1 requirement
   uncovered) · HIGH (conflict, duplicate, untestable AC, ambiguous security/privacy attribute)
   · MEDIUM (terminology drift, missing NFR task, underspecified edge case) · LOW (wording).
6. **Report** (Markdown, no writes):
   findings table `ID | Category | Severity | Location | Summary | Recommendation` ·
   coverage table `Requirement | Has task? | Task ids | Test named?` · constitution/ADR issues
   · unmapped tasks · metrics (requirements, tasks, coverage %, ambiguity, duplication,
   critical count).
7. **Next actions**: CRITICAL → resolve before `/sdd-implement`, naming the owning command
   (`/sdd-specify` or `/sdd-clarify` for requirement issues, `/sdd-plan` for design,
   `/sdd-tasks` to regenerate). Offer: "Suggest concrete remediation edits for the top N?" —
   apply only after explicit approval, through the owning command.

## Done when

- [ ] Report produced with findings, coverage table and metrics; zero files modified
- [ ] Every CRITICAL names the artefact and command that must fix it
