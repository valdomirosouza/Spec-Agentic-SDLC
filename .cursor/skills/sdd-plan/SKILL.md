---
name: sdd-plan
description: Produce the implementation plan for an approved feature spec (Phase 5 — Architecture & Technical Design): plan.md with a Constitution Check gate, research.md, data-model.md, contracts/ and quickstart.md, plus the ADR / threat-model / DPIA decisions this repository requires. Trigger on "plan", "technical design", "architecture for the spec". Usage — /sdd-plan <stack, architecture and constraints>.
---

<!-- generated from .claude/skills/sdd-plan/SKILL.md by scripts/python/render_commands.py — edit the source, then re-render (ADR-0091) -->

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->
# /sdd-plan — approved spec → design artefacts

Adapted from spec-kit `/speckit.plan`; extended with the Phase 5 obligations of ADR-0058
(ADR, threat model, DPIA, observability design) and the Constitution Check against
`memory/constitution.md`.

## User input

```text
$ARGUMENTS
```

## Skills — load before executing (≤ 2)

`skills/domain/domain-modeling.md` · plus the one domain skill the feature needs
(`skills/api/rest-api-design.md`, `skills/observability/otel-instrumentation.md`,
`skills/ai/harness.md`, …). A third means the plan should be split into two specs (roadmap).

## Procedure

1. **Setup**: `scripts/bash/check-prerequisites.sh --json --require-spec --require-approved`
   (the gate refuses a spec that is not `approved`/`implemented` — Constitution I). Then
   `scripts/bash/setup-plan.sh --json` → `IMPL_PLAN`, `RESEARCH`, `DATA_MODEL`, `QUICKSTART`,
   `CONTRACTS` (copies `templates/{plan,research,data-model,quickstart,contracts-README}-template.md`;
   never overwrites an existing file).
2. **Load** spec.md, `memory/constitution.md`, governing ADRs from the frontmatter,
   `specs/system/architecture.md`, and the adopting repository's service registry (`services.yaml`)
   when topics/services are involved and the file exists.
3. **Technical Context**: fill every field; unknowns become `NEEDS CLARIFICATION` items that
   Phase 0 research must resolve. Never guess a library version or API (Constitution IX).
4. **Constitution Check** (gate): answer every article row with pass / justified / FAIL.
   A FAIL stops the command with the violation and the spec/plan change needed. "Justified"
   rows get a line in Complexity Tracking.
5. **Phase 5 obligations**: decide and record ADR required? (draft
   `docs/adr/ADR-NNNN-<slug>.md` from the ADR template, status Draft; > 3 ADRs touched at once
   is an `[HITL-ESCALATE]`), threat-model delta?, DPIA/RIPD?, Phase 10 mandatory?
6. **Phase 0 → research.md** (`templates/research-template.md`): one entry per
   unknown/dependency/integration with Decision, Rationale, Alternatives considered, Grounded in.
   Ground each claim (codebase → docs → Context7 → web → `uncertain — verify`).
7. **Phase 1 → data-model.md, contracts/, quickstart.md** (`templates/data-model-template.md`,
   `contracts-README-template.md`, `quickstart-template.md`): entities with fields, validation
   rules and state transitions; OpenAPI/AsyncAPI/Avro deltas (topics registered in the adopting
   repository's service registry when it has one); runnable validation scenarios, one per AC
   (prerequisites, commands, expected outcome — no implementation bodies).
8. **Observability Design** table (CUJ, metrics/spans, SLO entry, dashboard/runbook, rollback
   indicator) — Constitution VI. Re-run the Constitution Check after design.
9. **Human gates**: architecture approval is mandatory when an ADR or threat model is
   required (ADR-0058 gate 3). Leave the ADR in Draft and say so.

## Completion report

`IMPL_PLAN`, artefacts generated, Constitution Check summary, ADR/threat-model/DPIA decisions,
open `NEEDS CLARIFICATION` left for research, next command (`/sdd-checklist` for reviewer
checklists, then `/sdd-tasks`).

## Done when

- [ ] plan.md complete, Constitution Check has no FAIL, Complexity Tracking filled if needed
- [ ] research.md, data-model.md, contracts/, quickstart.md written
- [ ] ADR / threat model / DPIA decisions recorded; ADR drafted if required
