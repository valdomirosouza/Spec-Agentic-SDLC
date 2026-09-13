# Requirements Checklist: Log-Based Golden Signals

**Purpose**: built-in spec-quality gate maintained by `/sdd-specify` and `/sdd-clarify`
**Created**: 2026-09-12
**Feature**: `specs/features/SPEC-LGS-001-log-based-golden-signals/spec.md`
**Reviewer**: Tech Lead (spec quality) · DPO (CHK006) · Security Lead (CHK009)

**Semantics**: a checklist is a set of **unit tests for the requirements**, not for the code.
`[x]` means the reviewer judged the requirements-quality criterion satisfied; it never means the
implementation is done. `/sdd-implement` reads checkbox state as a gate and must not change it.

## Requirement Completeness

- [x] CHK001 Are requirements defined for every scenario class (primary, alternate, error, recovery)? [Coverage, Spec §2, §2 Edge Cases]
- [x] CHK002 Are non-functional requirements classified by the NFR taxonomy with an evidence gate? [Completeness, Spec §5]
- [x] CHK003 Are the mandatory sections (§2, §4, §6, §9, §10) filled with real content, no placeholders? [Completeness]

## Requirement Clarity

- [x] CHK004 Is every vague adjective ("real-time", "suitable") quantified? [Clarity, Spec §5 NFR-07, §6 SC-01/SC-04]
- [x] CHK005 Do all `[NEEDS CLARIFICATION]` markers have a recorded answer in §Clarifications? [Ambiguity — none remain]
- [x] CHK006 Are boundary conventions (>=, >, left-closed/right-open) stated so two implementations agree? [Clarity, Spec §Clarifications]

## Compliance & Privacy _(Constitution III, LGPD/GDPR)_

- [x] CHK007 Is every PII field classified L1–L4 with its masking point named? [Completeness, Spec §7 — `client_ip` L2, masked at ingestion]
- [ ] CHK008 Is the DPIA/RIPD decision recorded with a rationale? [Traceability, Spec §7, §13 A2 — RIPD yes; full-DPIA decision awaits the DPO]
- [x] CHK009 Are retention and data-subject-rights requirements specified for new data? [Gap — retention FR-06; masked IPs are not re-identifiable, no DSAR path needed, stated in §7]

## Security _(Constitution IV)_

- [x] CHK010 Are authentication and authorization requirements stated for every new resource? [Coverage, Spec §4 FR-10]
- [ ] CHK011 Is the threat-surface delta described with STRIDE categories and mitigations? [Completeness, Spec §7 — STRIDE pass over the ingestion boundary pending Security Lead]
- [x] CHK012 Are the touched OWASP ASVS / LLM controls named in the control matrices? [Traceability, Spec §7]

## Observability _(Constitution VI)_

- [x] CHK013 Are all four Golden Signals derived and their exposure named? [Completeness, Spec §8]
- [x] CHK014 Is the SLO impact and rollback indicator specified? [Measurability, Spec §8, plan.md Observability Design]

## Traceability & Audit _(Constitution VII)_

- [x] CHK015 Does every FR map to ≥ 1 AC and does the coverage footer show 0 unmapped? [Traceability, Spec §10 — 14/14]
- [x] CHK016 Does every AC name the test that will verify it? [Traceability, Spec §9]
- [x] CHK017 Are governing ADRs listed and does any new decision have a `new_adrs_required` slug? [Traceability — ADR-0066…0069 already Accepted; none required]

## Notes

- Two items stay open on purpose: CHK008 (DPO) and CHK011 (Security Lead) are reviewer decisions
  the agent must not take. `/sdd-implement` will stop on them and ask "proceed anyway?" — that is
  the gate working as designed.
