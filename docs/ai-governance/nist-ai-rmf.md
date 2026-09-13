<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# NIST AI RMF 1.0 — coverage by category

> **Framework:** NIST AI 100-1, AI Risk Management Framework 1.0 (January 2023).
> **Owner:** AI Governance Lead · **Assessed:** 2026-09-13 · **Against:** `main`
> **Companions:** [`eu-ai-act-compliance.md`](eu-ai-act-compliance.md) (what the law requires),
> [`../compliance/iso42001-scope-and-soa.md`](../compliance/iso42001-scope-and-soa.md) (how the
> management system runs).

## How to read this

The previous version of this page mapped the four functions in narrative tables with no framework
identifiers, which made it impossible to compare against the NIST Playbook, against a sector
profile, or against another organisation's assessment. This version is organised by the
framework's own **category identifiers**.

The AI RMF Core has four functions, **19 categories** and **72 subcategories**:

| Function    | Categories          | Subcategories |
| ----------- | ------------------- | ------------- |
| **GOVERN**  | GOVERN 1 – GOVERN 6 | 19            |
| **MAP**     | MAP 1 – MAP 5       | 18            |
| **MEASURE** | MEASURE 1 – MEASURE 4 | 22          |
| **MANAGE**  | MANAGE 1 – MANAGE 4 | 13            |
| **Total**   | 19                  | **72**        |

**Non-fabrication note (Constitution IX).** Category *themes* below are our own summary of what
each category addresses, written from the corpus's perspective. Individual **subcategory titles
are not reproduced**: their exact wording lives in NIST AI 100-1 and the Playbook, and restating
72 of them from memory would risk inventing framework text. Subcategory identifiers are cited only
where they were verified against a published source; those appear in the *Verified subcategories*
section. Completing the per-subcategory mapping against the Playbook export is tracked as a
remediation item.

**Coverage vocabulary.** `strong` — the outcome is achieved and something enforces it ·
`partial` — an artefact exists, a named gap remains · `gap` — no artefact addresses the outcome.

## Profile

This assessment uses a **use-case profile for a human-supervised agentic software-delivery
system**: an AI system that proposes and executes actions in a software repository under a
mandatory human-in-the-loop gateway, consuming a third-party foundation model. Categories about
third-party foundation-model *development* are assessed from the deployer's position, consistent
with [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) §1.

## GOVERN — policies, processes and accountability

| Category     | Theme                                                     | Coverage | Evidence                                                                                                   | Gap                                                                     |
| ------------ | --------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **GOVERN 1** | Legal and regulatory requirements understood and managed   | partial  | `specs/compliance/eu-ai-act-control-matrix.yaml`, ADR-0093, `docs/compliance/iso42001-scope-and-soa.md`      | LGPD and GDPR are mapped; sector-specific AI rules are not surveyed      |
| **GOVERN 2** | Accountability structures, roles, training                 | partial  | `docs/governance/raci-matrix.md`, `CLAUDE.md` §8, named leads per path                                       | No AI-specific competence or training requirement (ISO 42001 cl. 7.2)   |
| **GOVERN 3** | Workforce diversity, equity, inclusion and accessibility   | gap      | —                                                                                                            | Not addressed anywhere in the corpus                                     |
| **GOVERN 4** | Organisational culture: critical thinking, safety-first    | strong   | `memory/constitution.md` Art. V and IX, escalation protocol (ADR-0034), `[HITL-ESCALATE]` as a first-class outcome | Culture is encoded for agents, not measured for people                  |
| **GOVERN 5** | Engagement with AI actors and affected communities         | gap      | Reporting channel in `skills/ethics/ethical-ai-review.md`                                                    | No feedback path from affected individuals; no external consultation    |
| **GOVERN 6** | Policies for third-party software, data and models         | partial  | `docs/dependency-manifest.yaml`, `docs/compliance/dependency-policy.md`, ADR-0051 model contracts            | No supplier assessment criteria for AI providers; sub-processor register open (#37) |

## MAP — context and risk identification

| Category  | Theme                                                          | Coverage | Evidence                                                                                        | Gap                                                                        |
| --------- | -------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| **MAP 1** | Context established: intended purpose, setting, norms           | strong   | Spec template §1–§3, risk class at Phase 0, `docs/ai-governance/autonomy-boundaries.md`          | Intended purpose is per feature; no single system-level statement until #38 |
| **MAP 2** | AI system categorised: task, method, knowledge limits           | partial  | `specs/ai/agent-design.md`, `specs/ai/harness-design.md`, `docs/ai/model-lifecycle.md`           | Knowledge limits of the model are not stated; model card is a blank template (#38) |
| **MAP 3** | Benefits and costs of the AI capability understood              | partial  | `harness/business-value-check.yml`, value hypothesis at Phase 0, ADR-0020 cost envelope         | Benefits are stated per feature; no comparison against a non-AI baseline    |
| **MAP 4** | Risks and benefits mapped for all components, incl. third party | partial  | Threat models, `specs/security/owasp-genai-control-matrix.yaml`, DPIAs                            | No single AI risk register (REM-016)                                        |
| **MAP 5** | Impacts to individuals, groups and society characterised        | partial  | DPIA and RIPD, `skills/ethics/ethical-ai-review.md` bias audit                                   | Societal and environmental impact are not assessed (ISO 42001 A.5 gap)     |

## MEASURE — analysis, assessment and tracking

| Category      | Theme                                                          | Coverage | Evidence                                                                                          | Gap                                                                       |
| ------------- | -------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **MEASURE 1** | Appropriate methods and metrics identified and applied          | partial  | `docs/ai/eval-scorecard.md` (evaluator threshold 0.75), groundedness ≥ 0.9 as an SLI (ADR-0080)     | No declared accuracy metric per intended purpose (shared with EU AI Act Art. 15) |
| **MEASURE 2** | Trustworthy characteristics evaluated: validity, safety, security, privacy, fairness, explainability | partial | Abuse cases (ADR-0050), model behavioural contracts (ADR-0051), PII leakage tests, quarterly bias audit | Explainability is not measured; no fairness result has been recorded        |
| **MEASURE 3** | Mechanisms for tracking identified risks over time              | partial  | `specs/compliance/ai-post-market-monitoring.md` (#27), behavioural monitoring (ADR-0049)            | No monitoring cycle executed; drift has a metric but no threshold           |
| **MEASURE 4** | Feedback from domain experts and users gathered and assessed    | partial  | `specs/ai/feedback-loop.md`, Phase 14 retrospectives                                                | No channel for people affected by an agent action (shared with GOVERN 5)    |

## MANAGE — prioritisation, response and recovery

| Category     | Theme                                                        | Coverage | Evidence                                                                                              | Gap                                                                  |
| ------------ | ------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **MANAGE 1** | Risks prioritised, responded to and managed                   | partial  | Phase 10 gate, risk class at Phase 0, `docs/compliance/remediation-register.md`                         | Prioritisation is per feature; no residual-risk acceptance record (REM-016) |
| **MANAGE 2** | Strategies to maximise benefit and minimise negative impact   | strong   | HITL gateway (ADR-0011), autonomy levels (ADR-0015), sandbox (ADR-0016), the `PreToolUse` guard         | —                                                                       |
| **MANAGE 3** | Third-party risks managed, including pre-trained models       | partial  | Model behavioural contracts with a recorded BLOCKED verdict, dependency manifest, model registry (#42) | Provider's systemic-risk determination is not retained as evidence       |
| **MANAGE 4** | Post-deployment monitoring, appeal, override, decommissioning | partial  | Model lifecycle states, rollback by re-pinning the model, AI incident runbook (#40)                     | No appeal path for a person affected by an agent action                 |

## Verified subcategories

These subcategory identifiers were verified against published sources during this assessment and
are the only ones cited by number in the corpus:

| Subcategory    | What it addresses (verified)                                      | Where we stand                                                          |
| -------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **GOVERN 1.1** | Legal and regulatory requirements are understood and managed       | partial — EU AI Act and privacy mapped, sector rules not surveyed        |
| **MAP 2.3**    | Scientific integrity and TEVV considerations                       | partial — cited in `specs/ethics/ethical-ai-principles.md`               |
| **MAP 5.1**    | Likelihood and magnitude of impacts are documented                 | partial — DPIAs document impact; likelihood is not quantified            |
| **MEASURE 2.11** | Fairness and bias are evaluated                                  | partial — quarterly procedure defined, no result recorded                |
| **MANAGE 4.1** | Post-deployment monitoring, appeal and override, decommissioning   | partial — monitoring and override exist, no appeal path                  |

## The three honest headlines

1. **GOVERN 3 and GOVERN 5 are empty.** Workforce diversity and engagement with affected
   communities have no artefact at all. They are the only two categories with no evidence.
2. **MEASURE is the weakest function.** Every category is partial. The corpus measures the
   *agent's* output well and the *system's* fairness, explainability and drift barely.
3. **MANAGE 2 is the strongest category in the framework for this system**, and it is the one the
   corpus enforces executably rather than only documenting.

## Remediation

Category gaps feed [`../compliance/remediation-register.md`](../compliance/remediation-register.md).
Completing the per-subcategory mapping against the NIST Playbook export is REM-019.

## Related

- [`eu-ai-act-compliance.md`](eu-ai-act-compliance.md) · [`../compliance/iso42001-scope-and-soa.md`](../compliance/iso42001-scope-and-soa.md)
- [`ai-safety-checklist.md`](ai-safety-checklist.md) — the Phase 10 gate
- [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) — role and classification
