# [CHECKLIST TYPE] Checklist: [FEATURE NAME]

**Purpose**: [what this checklist covers]
**Created**: [DATE]
**Feature**: `specs/features/[SPEC-ID]-[slug]/spec.md`
**Reviewer**: [role — e.g. Security Lead, DPO, SRE Lead]

**Semantics**: a checklist is a set of **unit tests for the requirements**, not for the code.
`[x]` means the reviewer judged the requirements-quality criterion satisfied; it never means the
implementation is done. `/sdd-implement` reads checkbox state as a gate and must not change it.
`checklists/requirements.md` is the built-in spec-quality checklist maintained by `/sdd-specify`
and `/sdd-clarify`; every other checklist here is reviewer-owned.

<!--
  Item pattern: "Are/Is <requirement aspect> defined/quantified/consistent …? [Dimension, Spec §X]"
  Dimensions: Completeness · Clarity · Consistency · Measurability · Coverage · Edge Case · Gap ·
  Ambiguity · Conflict · Assumption · Traceability. ≥ 80% of items cite a spec section or marker.
  Prohibited: "Verify/Test/Confirm that the system …" — that is a test case, not a checklist item.
-->

## Requirement Completeness

- [ ] CHK001 Are requirements defined for every scenario class (primary, alternate, error, recovery)? [Coverage]
- [ ] CHK002 Are non-functional requirements classified by the NFR taxonomy with an evidence gate? [Completeness, Spec §5]

## Requirement Clarity

- [ ] CHK003 Is every vague adjective ("fast", "secure", "robust") quantified? [Clarity]
- [ ] CHK004 Do all `[NEEDS CLARIFICATION]` markers have a recorded answer in §Clarifications? [Ambiguity]

## Compliance & Privacy _(Constitution III, LGPD/GDPR)_

- [ ] CHK005 Is every PII field classified L1–L4 with its masking point named? [Completeness, Spec §7]
- [ ] CHK006 Is the DPIA/RIPD decision recorded with a rationale? [Traceability, Spec §7]
- [ ] CHK007 Are retention and data-subject-rights requirements specified for new data? [Gap]

## Security _(Constitution IV)_

- [ ] CHK008 Are authentication and authorization requirements stated for every new resource? [Coverage]
- [ ] CHK009 Is the threat-surface delta described with STRIDE categories and mitigations? [Completeness, Spec §7]
- [ ] CHK010 Are the touched OWASP ASVS / LLM controls named in the control matrices? [Traceability]

## Observability _(Constitution VI)_

- [ ] CHK011 Are all four Golden Signals derived and their exposure named? [Completeness, Spec §8]
- [ ] CHK012 Is the SLO impact and rollback indicator specified? [Measurability]

## Traceability & Audit _(Constitution VII)_

- [ ] CHK013 Does every FR map to ≥ 1 AC and does the coverage footer show 0 unmapped? [Traceability, Spec §10]
- [ ] CHK014 Does every AC name the test that will verify it? [Traceability, Spec §9]
- [ ] CHK015 Are governing ADRs listed and does any new decision have a `new_adrs_required` slug? [Traceability]

## Notes

- Leave items unchecked while they still need clarification or reviewer judgement.
- Add findings inline; link to the spec section or ADR.
