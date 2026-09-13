<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ISO/IEC 42001 — AI management system: scope and Statement of Applicability

> **Standard:** ISO/IEC 42001:2023 — Information technology · Artificial intelligence ·
> Management system. **Owner:** AI Governance Lead · **Last reviewed:** 2026-09-13
> **Companion:** [`iso42001-annex-a-control-matrix.md`](iso42001-annex-a-control-matrix.md) ·
> **Gaps:** [`remediation-register.md`](remediation-register.md)
>
> **Copyright note.** ISO/IEC 42001 is a licensed standard. Clause and control **titles are
> paraphrased** and the normative text is **not reproduced**. Anyone operating this management
> system needs the licensed copy; this page records *our decisions*, not the standard.

## 1. Why this exists

Before this page, ISO/IEC 42001 appeared exactly once in the corpus — in a baseline table in
`docs/template-structure.md`, with the coverage column filled in as "All clauses". That is an
assertion with nothing behind it. ISO/IEC 27001 has an Annex A self-assessment; the AI management
system had none, even though the corpus governs an agentic AI system end to end.

ISO/IEC 42001 is the management-system counterpart to the EU AI Act work in
[ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md): the Act says *what*
obligations bind, the standard says *how an organisation runs a system that keeps meeting them*.
The two share evidence and are reviewed together.

## 2. Scope of the AI management system

**In scope.** The design, development, delivery, operation and retirement of the agentic AI system
governed by this corpus: the agents, their guardrails, the human-in-the-loop gateway, the
autonomy model, the prompts, the retrieval corpus, the agent memory, and the third-party
foundation model consumed under the organisation's own authority.

**Out of scope.** The foundation model's own training and development (the model provider's
management system), the adopting organisation's non-AI software, and any AI system a third party
places on the market under its own name.

**Interested parties and what they require.**

| Party                     | Requirement                                                                |
| ------------------------- | --------------------------------------------------------------------------- |
| Individuals affected      | Human oversight, transparency, no prohibited practice, redress              |
| The adopting organisation | Predictable delivery, auditable evidence, bounded autonomy                  |
| Regulators and auditors   | Traceability from obligation to artefact to test to release evidence        |
| Model provider            | Use within its acceptable-use terms; accurate reporting of incidents        |
| Engineering teams         | Rules that are executable, not only written                                 |

**Boundaries and interfaces.** The management system stops where the corpus stops. The adopting
product repository provides the code, tests, CI and service registry; the interface between them is
`docs/reference/adopter-provided-paths.md` and `SETUP.md` §2.

## 3. Clauses 4 to 10 — where each is satisfied

| Clause                              | What it asks for (paraphrase)                                | Where it lives here                                                                                      | State      |
| ----------------------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ---------- |
| **4** Context of the organisation   | Context, interested parties, scope, the management system    | §2 of this page                                                                                          | documented |
| **5** Leadership                    | Policy, roles, responsibilities and authorities              | `memory/constitution.md`, `docs/process/RACI.md`, `docs/governance/raci-matrix.md`                        | documented |
| **6** Planning                      | Risks and opportunities, AI objectives, change planning      | `docs/privacy/dpia/`, `docs/ai-governance/nist-ai-rmf.md`, `specs/compliance/eu-ai-act-control-matrix.yaml` | partial    |
| **7** Support                       | Resources, competence, awareness, communication, documented information | `skills/`, `CLAUDE.md`, `docs/process/`, the spec grammar (ADR-0085)                              | documented |
| **8** Operation                     | Operational planning and control, AI risk assessment and treatment, impact assessment | The 15-phase lifecycle (ADR-0058) with nine human gates, Phase 10 AI Safety           | documented |
| **9** Performance evaluation        | Monitoring, measurement, analysis, internal audit, management review | `docs/ai/eval-scorecard.md`, `docs/sre/slo/`, `specs/compliance/ai-post-market-monitoring.md`     | partial    |
| **10** Improvement                  | Nonconformity, corrective action, continual improvement      | `docs/postmortems/`, `docs/compliance/remediation-register.md`, Phase 14 retrospectives                   | partial    |

**The three partial clauses are the real gaps.** Clause 6 has risk assessment spread across DPIAs
and threat models with no single AI risk register. Clause 9 has no internal audit programme and no
recorded management review. Clause 10 has corrective action for incidents but no nonconformity
register for the management system itself.

## 4. Statement of Applicability — Annex A

Annex A of ISO/IEC 42001 offers **38 controls grouped under nine control objectives, A.2 to A.10**.
Clause 6.1.3 does not require adopting all of them: an organisation determines the controls its
risk treatment needs, then compares that set against Annex A to confirm nothing relevant was
overlooked. This Statement of Applicability records that comparison at objective level; the
per-control detail is in
[`iso42001-annex-a-control-matrix.md`](iso42001-annex-a-control-matrix.md).

| Objective | Theme (paraphrased)                    | Applicable | Our position                                                                                                     |
| --------- | -------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------- |
| **A.2**   | Policies related to AI                 | Yes        | `memory/constitution.md` is the AI policy; `specs/ethics/ethical-ai-principles.md` and `CLAUDE.md` §3 extend it   |
| **A.3**   | Internal organisation                  | Yes        | Roles and escalation in the RACI matrices and ADR-0034; the AI Governance Lead is named throughout                |
| **A.4**   | Resources for AI systems               | Partial    | Compute, data, tooling and human resources are named per feature in the plan template; no organisation-wide inventory until #42 |
| **A.5**   | Assessing impacts of AI systems        | Yes        | DPIA and RIPD with a release gate; ethical review; Phase 10 checklist                                             |
| **A.6**   | AI system life cycle                   | Yes        | The largest objective and the corpus's strongest area: the 15 phases, the `/sdd-*` commands, model lifecycle, evaluator thresholds, abuse cases |
| **A.7**   | Data for AI systems                    | Partial    | Privacy side is strong; provenance, quality and lineage of AI data arrive with issues #29, #32, #33, #34          |
| **A.8**   | Information for interested parties     | Partial    | System card and model card arrive with #38; user-facing disclosure for Art. 50 is not yet written                 |
| **A.9**   | Use of AI systems                      | Yes        | Autonomy boundaries, HITL/HOTL, dual-use registry (#39), acceptable use in the ethics skill                      |
| **A.10**  | Third-party and customer relationships | Partial    | Model provider terms and the dependency manifest exist; the sub-processor register arrives with #37              |

**Nothing is excluded as not applicable.** Four objectives are partial, each with a named artefact
that closes it. Exclusions, if any are ever claimed, require a justification recorded here and
approved by the AI Governance Lead — the same rule the EU AI Act matrix applies to `n/a`.

## 5. Certification posture

The organisation is **not pursuing certification today**. This Statement of Applicability exists so
that certification is a decision rather than a project restart: the scope, the clause mapping and
the objective-level applicability are already recorded, and the remediation register tracks the
gaps a certification audit would raise first — the internal audit programme (clause 9), the
management review (clause 9) and the AI risk register (clause 6).

Should certification be pursued, the sequence is: close the clause 6, 9 and 10 gaps, complete the
per-control matrix against the licensed standard text, run one internal audit cycle, hold one
management review, then engage a certification body.

## 6. Review

Reviewed annually and whenever ADR-0093 is amended, the scope changes, or an Annex A objective
moves between applicable and partial. Each review records the date and what changed.

| Date       | Change                                                                    |
| ---------- | ------------------------------------------------------------------------- |
| 2026-09-13 | Created. Scope, clause mapping and objective-level SoA recorded for the first time (#25) |

## Related

- [`iso42001-annex-a-control-matrix.md`](iso42001-annex-a-control-matrix.md) — objective-by-objective detail
- [`remediation-register.md`](remediation-register.md) — where the gaps are tracked
- [`iso27001-annex-a-control-matrix.md`](iso27001-annex-a-control-matrix.md) — the information-security counterpart
- [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) — the regulatory side of the same programme
