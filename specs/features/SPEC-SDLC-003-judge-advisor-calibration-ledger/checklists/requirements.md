# Requirements Checklist: Judge and Advisor calibration ledger

**Purpose**: the built-in spec-quality checklist maintained by `/sdd-specify` and `/sdd-clarify`
**Created**: 2026-11-16
**Feature**: `specs/features/SPEC-SDLC-003-judge-advisor-calibration-ledger/spec.md`
**Reviewer**: Tech Lead + Security Lead (Spec-as-PR)

**Semantics**: a checklist is a set of **unit tests for the requirements**, not for the code.
`[x]` means the requirements-quality criterion is satisfied. It never means the implementation is
done.

## Content Quality

- [x] CHK001 Is the spec free of implementation detail beyond what the requirements name? The scoring values and the n ≥ 10 floor are requirements (the Tech Lead's decision). The ledger's path, format and tooling are left to the plan (A2). [Clarity, Spec §4]
- [x] CHK002 Are all mandatory sections filled, with `N/A — reason` where a section does not apply? [Completeness, Spec §2, §4, §6, §8]

## Requirement Completeness

- [x] CHK003 Are all `[NEEDS CLARIFICATION]` markers answered? None were needed: the scope and scoring decisions were taken before drafting and are recorded in §Clarifications. [Ambiguity]
- [x] CHK004 Are the edge cases listed? These are late evidence, evidence that never arrives, an overridden `fail` followed by a defect, a missing verdict, two defects on one gate, and an advice-avoided failure. [Edge Case, Spec §2]
- [x] CHK005 Is the scope bounded? Routing and autonomy effects, demotion, the delegation flow, human scoring and the interim session ledger are excluded. [Coverage, Spec §3]

## Requirement Clarity & Measurability

- [x] CHK006 Is every FR EARS-phrased and testable through an AC? [Clarity, Spec §4, §9]
- [x] CHK007 Is every success criterion measurable without naming a technology? [Measurability, Spec §6]

## Traceability

- [x] CHK008 Does every FR map to at least one AC, with a coverage footer of K = 0? [Traceability, Spec §10]
- [x] CHK009 Does every AC name the test that will verify it, marked as planned for Phase 6? [Traceability, Spec §9]
- [x] CHK010 Are the governing ADRs listed? Is it stated that no new ADR is needed, because demotion (which would amend ADR-0070) is out of scope? [Traceability, frontmatter, Spec §3]

## Governance

- [x] CHK011 Is the PII and DPIA decision recorded with a rationale? There is no new personal data, so no DPIA, and human decisions are recorded by role. [Completeness, Spec §7]
- [x] CHK012 Are the Golden Signals derived and exposed, read per release? [Completeness, Spec §8]
- [x] CHK013 Is it stated that no score reaches a gate, an approval, routing, autonomy or the Judge's mode (Article V)? [Consistency, Spec §3, FR-10]
- [x] CHK014 Is scoring by agreement excluded? That covers agreement with the human and between the agents, and escalation scores 0 (Articles V and IX). [Consistency, FR-06, FR-07]

## Notes

- Pass 1 of 3: an independent Judge review returned `fail`. A `fail` the human accepted was scored by that agreement (CHK014). Some Advisor cases were unscored, the FR-08 metrics were undefined, and a citation pointed outside the corpus.
- Pass 2 of 3: the scoring rules now list every case, and unlisted cases score 0. A `fail` scores only on independent evidence. The FR-08 metrics are defined, and the automation-bias flag is withheld below n = 10. Every item passes. The spec stays `draft`, and approval is the Spec-as-PR review by the Tech Lead and the Security Lead.
