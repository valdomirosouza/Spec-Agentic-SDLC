---
name: sdd-checklist
description: Generate a reviewer-owned requirements-quality checklist ("unit tests for the requirements") for the active feature — security, privacy/LGPD-GDPR, observability, API, UX, audit — into specs/features/<id>/checklists/<domain>.md. Never tests the implementation; never ticks items. Trigger on "checklist", "review the requirements for", "unit tests for the spec". Usage — /sdd-checklist [domain or focus].
---

# /sdd-checklist — unit tests for the requirements

Adapted from spec-kit `/speckit.checklist`. A checklist validates the **writing** of the
requirements (complete, clear, consistent, measurable, covered), not whether the code works.

## User input

```text
$ARGUMENTS
```

## Procedure

1. `scripts/bash/check-prerequisites.sh --json --require-spec` → `FEATURE_DIR`, `AVAILABLE_DOCS`.
   Load `memory/constitution.md` and `templates/checklist-template.md`.
2. **Clarify intent** with up to three questions derived from the user's phrasing and the spec
   (scope, depth, audience, exclusions) — skip any already answered. Defaults when
   non-interactive: depth standard, audience PR reviewer, top two focus areas.
3. **Load context** surgically: spec.md sections relevant to the focus, plan.md and tasks.md if
   present. Summarise rather than dump.
4. **Generate** `FEATURE_DIR/checklists/<domain>.md` (create, or append continuing the last
   `CHK` id; never delete existing items; all new items unchecked). Group by quality dimension:
   Completeness · Clarity · Consistency · Acceptance-criteria quality · Scenario coverage ·
   Edge cases · Non-functional · Dependencies & assumptions · Ambiguities & conflicts.
   - Item pattern: "Are/Is <aspect> defined/quantified/consistent …? [Dimension, Spec §X]".
   - ≥ 80% of items carry a traceability reference (`Spec §`, `[Gap]`, `[Ambiguity]`,
     `[Conflict]`, `[Assumption]`).
   - Prohibited: "Verify / Test / Confirm that the system …", click/render/execute wording,
     implementation details.
   - Always include the repository's cross-cutting rows for the chosen domain:
     **privacy** (PII class, masking point, DPIA, retention, data-subject rights),
     **security** (authn/z per resource, STRIDE delta, control-matrix ids),
     **observability** (four Golden Signals, SLO impact, rollback indicator, runbook),
     **audit** (FR→AC coverage 0 unmapped, AC→test names, ADR ids, issue number).
5. Soft cap 40 items; merge near-duplicates; collapse many low-impact edge cases into one item.
6. **Ownership**: the reviewer named in the header ticks items. `/sdd-implement` reads the
   state as a gate; this command never marks anything `[x]`.

## Completion report

Path, item count, created vs appended, focus areas, depth, audience, must-have items included.

## Done when

- [ ] `checklists/<domain>.md` written per template, every item unchecked and traceable
- [ ] No item tests implementation behaviour
