---
id: SPEC-FEAT-NNN # SPEC-<DOMAIN>-<NNN>; unique; the feature directory is specs/features/<id>-<slug>/
kind: feature-spec # spec | policy | feature-spec | threat-model
status: draft # draft | in-review | approved | implemented | superseded (ADR-0085)
owner: <github-handle>
issue: null # GitHub issue number
governing_adrs: []
new_adrs_required: []
implemented_by: [] # filled at Phase 6
verified_by: [] # tests that prove the acceptance criteria
related_specs: []
roadmap: null # specs/features/<epic>/roadmap.md → entry R<n>, when this spec is a slice of an epic
last_updated: YYYY-MM-DD
---

# Feature Specification: [FEATURE NAME]

**Input**: <the user's feature description, verbatim or lightly trimmed>
**Risk class**: small-fix | normal | high | ai | security | infra _(Phase 0; picks the delivery tier)_

<!--
  HOW THIS TEMPLATE WORKS
  • Focus on WHAT users need and WHY. No tech stack, APIs or code structure here — that belongs
    in plan.md (Phase 5). Written for business stakeholders as much as engineers.
  • Every FR is EARS-phrased ("WHEN <trigger> the system SHALL <response>") and testable.
  • Every FR maps to ≥ 1 acceptance criterion (§Requirement Coverage). Unmapped FRs block DoR.
  • Mark genuine ambiguity as [NEEDS CLARIFICATION: specific question] — at most THREE. Make
    informed defaults for everything else and record them under Assumptions.
  • Sections marked (gate) are checked by docs/process/gates/phase-gates.yaml.
  • Merged from specs/SPEC-TEMPLATE.md (§ numbering, governance gates) and spec-kit's
    spec-template (prioritised, independently testable user stories; SC-/FR- ids; clarifications).
-->

## Clarifications

<!-- Filled by /sdd-clarify. One "### Session YYYY-MM-DD" per run; "- Q: … → A: …" per answer. -->

## 1. Context & Problem

### 1.1 Problem statement

### 1.2 Why now

## 2. User Scenarios & Testing _(mandatory)_

<!--
  Order stories by priority. Each story is INDEPENDENTLY TESTABLE: implementing only P1 still
  yields a demonstrable, deployable increment (the MVP). tasks.md is organised by these stories.
-->

### User Story 1 — [Title] (Priority: P1) 🎯 MVP

[Plain-language journey]

**Why this priority**: [value]

**Independent Test**: [how this story is verified on its own]

**Acceptance Scenarios**:

1. **Given** [state], **When** [action], **Then** [outcome]

### User Story 2 — [Title] (Priority: P2)

[…]

### Edge Cases

- What happens when [boundary condition]?
- How does the system behave on [error / empty / concurrent scenario]?

## 3. Non-Goals / Out of Scope

- [Explicitly excluded, to bound scope]

## 4. Functional Requirements _(mandatory)_

| ID    | Requirement (EARS: WHEN … the system SHALL …) | Story | Priority |
| ----- | --------------------------------------------- | ----- | -------- |
| FR-01 |                                               | US1   | must     |

_Example of a marked ambiguity — remove before approval:_
`FR-0X: The system SHALL authenticate users via [NEEDS CLARIFICATION: email/password, SSO, OAuth?]`

### Key Entities _(include if the feature involves data)_

- **[Entity]**: what it represents, key attributes, relationships (no storage details)

## 5. Non-Functional Requirements

<!-- Classify by docs/product/nfr-taxonomy.md. Flag every PII field here. -->

| ID     | Requirement | Category (taxonomy) | Evidence / gate |
| ------ | ----------- | ------------------- | --------------- |
| NFR-01 |             |                     |                 |

## 6. Success Criteria _(mandatory, measurable, technology-agnostic)_

| ID    | Measurable outcome                                   | Measurement |
| ----- | ---------------------------------------------------- | ----------- |
| SC-01 | e.g. "Operators approve a request in under 60 s p50" |             |

## 7. Governance, Privacy & Security _(gate: threat & privacy review)_

| Concern                                  | Control in this spec | Maps to                        |
| ---------------------------------------- | -------------------- | ------------------------------ |
| Human oversight (HITL/HOTL)              |                      | ADR-0011                       |
| PII (classify L1–L4; mask at boundaries) |                      | ADR-0012, specs/privacy/       |
| DPIA / RIPD required?                    | yes / no             | docs/privacy/dpia/             |
| Auditability (immutable trail)           |                      | ADR-0026                       |
| Authn / abuse (auth, rate limit)         |                      | specs/security/threat-model.md |
| OWASP controls touched                   |                      | specs/security/*.yaml          |

## 8. Golden Signals & SLO _(gate: observability)_

| Signal     | Derivation | Exposed as      |
| ---------- | ---------- | --------------- |
| Traffic    |            |                 |
| Latency    |            | P50 / P95 / P99 |
| Errors     |            | error_rate      |
| Saturation |            |                 |

## 9. Acceptance Criteria _(gate: canonical, machine-traceable)_

| ID    | Given / When / Then (one line) | Covers FR(s) | Verified by (test path or `requirement` marker)  |
| ----- | ------------------------------ | ------------ | ------------------------------------------------ |
| AC-01 |                                | FR-01        | `tests/…` — `requirement("SPEC-FEAT-NNN/FR-01")` |

## 10. Requirement Coverage _(gate)_

**Coverage footer.** _N_ FRs total · _M_ mapped to ≥ 1 AC · **_K_ unmapped ⚠️** (K must be 0 for DoR/DoD)

## 11. Risks & Limitations

- [Known trade-off → ADR consequence]

## 12. Open Questions

<!-- Resolved at a HITL gate, never assumed. Each item ends resolved/decided/deferred with an ADR,
     RFC or #issue reference before status: approved. "None." is valid. -->

None.

## 13. Assumptions

| #   | Assumption | Owner | Resolve by (phase) | Status (open / confirmed / rejected) |
| --- | ---------- | ----- | ------------------ | ------------------------------------ |
| A1  |            |       | 4 — Specification  | open                                 |

## 14. References

- Roadmap entry (if any), related specs, ADRs, prior art
