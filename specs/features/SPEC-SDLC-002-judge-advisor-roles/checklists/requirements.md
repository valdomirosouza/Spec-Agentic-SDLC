# Requirements Checklist: Dev-time Judge and Advisor roles

**Purpose**: built-in spec-quality checklist maintained by `/sdd-specify` and `/sdd-clarify`
**Created**: 2026-11-15
**Feature**: `specs/features/SPEC-SDLC-002-judge-advisor-roles/spec.md`
**Reviewer**: Tech Lead + Security Lead (Spec-as-PR)

**Semantics**: a checklist is a set of **unit tests for the requirements**, not for the code.
`[x]` means the requirements-quality criterion is satisfied; it never means the implementation is
done.

## Content Quality

- [x] CHK001 Is the spec free of implementation detail beyond the artefacts the requirement names? Agent names, the verdict fields and the state location are named, because they are what the roles are. Prompt text, tool lists and storage formats are left to the plan. [Clarity, Spec §4]
- [x] CHK002 Are all mandatory sections filled, with `N/A — reason` where a section does not apply? [Completeness, Spec §2, §4, §6, §8]

## Requirement Completeness

- [x] CHK003 Are all `[NEEDS CLARIFICATION]` markers answered and recorded in §Clarifications? Q1, Q2 and Q3 were answered on 2026-11-15, and Q3 added FR-20 and AC-13. [Ambiguity]
- [x] CHK004 Are edge cases listed, namely Judge error, missing rubric, missing ACs, same model, advice to weaken a gate, and a human overriding a `fail`? [Edge Case, Spec §2]
- [x] CHK005 Is scope bounded, with P4 to P6, blocking mode, other phases and other triggers excluded? [Coverage, Spec §3]

## Requirement Clarity & Measurability

- [x] CHK006 Is every FR EARS-phrased and testable through an AC? [Clarity, Spec §4, §9]
- [x] CHK007 Is every success criterion measurable without naming a technology? [Measurability, Spec §6]

## Traceability

- [x] CHK008 Does every FR map to at least one AC, with a coverage footer of K = 0? [Traceability, Spec §10]
- [x] CHK009 Does every AC name the test that will verify it, each marked as planned for Phase 6? [Traceability, Spec §9]
- [x] CHK010 Are the governing ADRs listed, and does the new decision carry a `new_adrs_required` slug? [Traceability, frontmatter]

## Governance

- [x] CHK011 Is the PII and DPIA decision recorded with a rationale? No new personal data, so no DPIA. [Completeness, Spec §7]
- [x] CHK012 Are the Golden Signals derived and exposed, read per run and per release? [Completeness, Spec §8]
- [x] CHK013 Is it stated that no human gate or approval is removed or satisfied by an agent (Article V)? [Consistency, Spec §3, FR-08, FR-17]

## Notes

- Pass 2 of 3: every item passes. Approval is the Spec-as-PR review by the Tech Lead and the Security Lead.
