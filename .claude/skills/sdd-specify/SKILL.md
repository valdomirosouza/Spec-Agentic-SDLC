---
name: sdd-specify
description: Turn a natural-language feature description into a feature specification under specs/features/<SPEC-ID>-<slug>/spec.md (Phase 4 of ADR-0058), with prioritised user stories, EARS requirements, measurable success criteria, at most three [NEEDS CLARIFICATION] markers, and the built-in requirements checklist. Trigger on "specify", "write the spec", "new feature spec". Usage — /sdd-specify <feature description>.
---

# /sdd-specify — feature description → specification

Adapted from spec-kit `/speckit.specify`, bound to this repository's spec grammar (ADR-0085),
the 15-phase lifecycle (ADR-0058) and Constitution I and IX.

## User input

```text
$ARGUMENTS
```

The text after the command **is** the feature description. If it is empty, stop and ask for it.

## Skills — load before executing (≤ 2, ADR-0060)

`skills/sdlc/spec-lifecycle.md` · one domain skill picked from the description (e.g.
`skills/privacy/pii.md` when personal data is involved, `skills/api/rest-api-design.md` for an API).

## Procedure

1. **Create the feature directory**: run `scripts/bash/create-new-feature.sh --json "<description>"`
   (add `--domain <DOMAIN>` for non-FEAT domains, `--issue <N>` when the GitHub issue exists).
   Parse `SPEC_ID`, `FEATURE_DIR`, `SPEC_FILE`, `BRANCH_NAME`. The script never creates a git
   branch; tell the user the suggested branch name (`feature/<SPEC-ID>-<slug>`, CLAUDE.md §6).
2. **Load context**: `memory/constitution.md`; `docs/glossary.md` for terms; if the description
   names an epic roadmap, the roadmap entry (`templates/roadmap-template.md` convention).
3. **Write the spec** into `SPEC_FILE` following `templates/spec-template.md` exactly:
   - Extract actors, actions, data, constraints. Assign a risk class (Phase 0 vocabulary:
     small-fix / normal / high / ai / security / infra).
   - User stories ordered P1…Pn, each **independently testable**, with Given/When/Then scenarios.
   - Functional requirements EARS-phrased, each mapped to a story; success criteria measurable
     and technology-agnostic; NFRs classified by `docs/product/nfr-taxonomy.md`.
   - Governance table (§7): PII class, DPIA decision, HITL route, OWASP controls touched.
   - Golden Signals (§8) and canonical AC table (§9) with `requirement("SPEC-…/FR-NN")` markers.
   - **Ambiguity policy**: make informed defaults and record them in §13 Assumptions. Use
     `[NEEDS CLARIFICATION: question]` only when the choice changes scope, security/privacy or
     UX and no reasonable default exists — **maximum three**, prioritised scope > security/privacy
     > UX > technical. Never invent an API, path or ADR number (Constitution IX).
   - Frontmatter: `status: draft`, `governing_adrs` from `docs/adr/README.md`, `issue`.
4. **Requirements checklist**: create `FEATURE_DIR/checklists/requirements.md` from
   `templates/checklist-template.md` with the built-in items: no implementation details; all
   mandatory sections filled; no `[NEEDS CLARIFICATION]` left; requirements testable and
   unambiguous; success criteria measurable; edge cases listed; scope bounded; every FR mapped
   to ≥ 1 AC (coverage footer K = 0); PII/DPIA decision recorded; Golden Signals filled.
   Evaluate each item; fix the spec and re-evaluate (max three passes).
5. **Clarifications pending?** If markers remain, present each as a numbered question with a
   recommended answer and an options table, all at once, and wait. Encode answers into the spec
   (`## Clarifications` → `### Session YYYY-MM-DD`) and remove the markers.
6. **Human gate**: the spec stays `draft`. Approval (`status: approved`) happens through the
   Spec-as-PR review by Tech Lead + Security Lead (docs/process/HITL-GOVERNANCE.md). Never set
   `approved` yourself.

## Completion report

`SPEC_ID`, `FEATURE_DIR`, `SPEC_FILE`, suggested branch, risk class, checklist pass count,
open clarifications, next command (`/sdd-clarify` if anything is Partial/Missing, else
`/sdd-plan` once the spec is approved).

## Done when

- [ ] spec.md written with valid ADR-0085 frontmatter and every template section
- [ ] checklists/requirements.md created and evaluated
- [ ] ≤ 3 clarification markers, each presented to the user
- [ ] Status left as `draft`; approval path stated
