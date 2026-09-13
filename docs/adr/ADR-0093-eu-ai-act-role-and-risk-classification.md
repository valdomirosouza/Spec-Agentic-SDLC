<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0093 — EU AI Act: Role, Risk Classification and the Obligations They Trigger

**Status:** Accepted
**Date:** 2026-09-13
**Authors:** AI Governance Lead (drafted with Claude Code)
**Spec:** `specs/compliance/eu-ai-act-control-matrix.yaml` · `docs/ai-governance/eu-ai-act-compliance.md`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0011](ADR-0011-hitl-hotl-model.md) (HITL/HOTL), [ADR-0015](ADR-0015-feature-flag-strategy.md) (autonomy flags), [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation), [ADR-0051](ADR-0051-model-behavioral-contracts.md) (model contracts), [ADR-0072](ADR-0072-versioned-security-control-matrices.md) (control-matrix pattern)

---

## Context

`docs/ai-governance/eu-ai-act-compliance.md` asserted a classification — "High-Risk (automated
decision-making with real-world effects)" — in a table cell, without naming the role the
organisation plays, without citing Article 6 or Annex III, and without deriving which obligations
follow or from when. Everything downstream (which articles are mandatory, which artefacts must
exist, which dates bind) depends on that classification, so an unexplained cell is the weakest
possible foundation: it cannot be audited, contested, or re-derived when the system changes.

Regulation (EU) 2024/1689 makes three determinations independent of one another:

1. **Which role you play.** Provider, deployer, importer, distributor or authorised
   representative. The obligations differ sharply; the same organisation is frequently both a
   provider (of the agentic system it builds) and a deployer (of the third-party model it calls).
2. **Which risk tier the AI system falls in.** Prohibited (Art. 5), high-risk (Art. 6 together
   with Annexes I and III), limited-risk with transparency duties (Art. 50), or minimal risk.
3. **Whether a general-purpose AI model is involved** and, if so, whether it carries systemic
   risk (Arts. 51–55) — a separate regime that attaches to the *model*, not to the system.

This corpus describes a governance layer for an agentic system whose real-world effects are
mediated by a mandatory human-in-the-loop gateway (ADR-0011) and whose autonomy is granted only
through governed feature flags (ADR-0015). The corpus itself processes no personal data and makes
no automated decisions; the **adopting product repository** does.

Article headings, numbering and application dates below were verified against the published
structure of Regulation (EU) 2024/1689 on 2026-09-13 (see §Grounding). Dates have been amended
since the original text; they are re-verified at every review of this ADR.

## Decision

### 1. Role

For the system this corpus governs, the adopting organisation is:

| Role                                                   | Applies | Rationale                                                                                            |
| ------------------------------------------------------ | ------- | ---------------------------------------------------------------------------------------------------- |
| **Provider** of the agentic AI system                  | **Yes** | It develops the system and places it on the market or into service under its own name                |
| **Deployer** of a third-party general-purpose AI model | **Yes** | It uses a foundation model under its own authority (`docs/dependency-manifest.yaml` pins the version) |
| Provider of a general-purpose AI model                 | No      | It does not train or place a GPAI model on the market; Arts. 53 and 55 bind the model's provider      |
| Importer / distributor / authorised representative     | No      | No third-party AI system is placed on the market under another provider's name                        |

**Consequence.** Provider obligations for the AI system (Arts. 16–21) and deployer obligations
toward the upstream model apply together. The corpus must therefore carry both the provider's
technical file and the evidence a deployer owes.

### 2. Risk classification of the AI system

**The agentic system is classified as high-risk, and the classification is conditional on the use
case of the adopting repository, not on the technology.** The determination is made in this order
and recorded per adoption:

1. **Article 5 — prohibited practices.** The system MUST NOT implement any practice listed in
   Article 5. This is not a risk tier to be managed; it is a hard prohibition. Every prohibited
   practice is carried as a control with status `prohibited` in the EU AI Act control matrix, and
   a spec that would implement one is refused at the Phase 10 gate, not mitigated.
2. **Article 6(1) with Annex I.** Not applicable: the system is not a safety component of a
   product covered by the Union harmonisation legislation in Annex I.
3. **Article 6(2) with Annex III.** **Applicable by default in this corpus.** An agentic system
   that proposes and executes actions with real-world effects falls into an Annex III area
   whenever the adopting repository uses it for any of: employment and worker management,
   access to essential private or public services and benefits, creditworthiness, biometrics,
   critical infrastructure, education, law enforcement, migration, or administration of justice.
   The corpus therefore assumes high-risk and requires the adopter to **narrow** the
   classification with evidence, never to widen it silently.
4. **Article 6(3) derogation.** An adopter may conclude the system is *not* high-risk when it only
   performs a narrow procedural task, improves the result of a previously completed human
   activity, detects decision patterns without replacing human assessment, or performs a
   preparatory task. Invoking the derogation is a **documented assessment registered before
   use**, approved by the AI Governance Lead and the Legal owner, and recorded as an amendment to
   this ADR — never an implicit conclusion.
5. **Article 50 — transparency.** Applies **regardless of the tier above** whenever the system
   interacts directly with people, generates or manipulates synthetic content, or performs
   emotion recognition or biometric categorisation. In an agentic system that answers humans,
   Article 50 is assumed to apply.

### 3. Classification of the model

The foundation model called by the system is a **general-purpose AI model** provided by a third
party. The adopting organisation is its deployer, not its provider. Two consequences:

- Arts. 53 and 55 bind the model's provider; the adopter's duty is to **obtain and retain** the
  information the provider is required to supply, and to record it in the model card and the
  model registry (issue #38, #42).
- Whether the specific model carries **systemic risk** (Art. 51) is the provider's determination.
  The adopter records the provider's published determination rather than asserting its own.

### 4. Obligations this classification triggers

| Obligation                                                             | Article        | Artefact in this corpus                                                       |
| ---------------------------------------------------------------------- | -------------- | ----------------------------------------------------------------------------- |
| No prohibited practice                                                 | 5              | Control matrix entries with status `prohibited`; Phase 10 gate                |
| Risk management system across the lifecycle                            | 9              | `docs/privacy/dpia/`, NIST AI RMF mapping, threat models                       |
| Data and data governance for training, validation and testing data     | 10             | Dataset datasheets, training-data policy, data-governance charter (#33, #34, #28) |
| Technical documentation                                                | 11 + Annex IV  | System card + model card + control matrix (#38)                               |
| Automatic record-keeping (logs)                                        | 12             | Immutable audit trail (ADR-0026), agent span conventions                       |
| Transparency and information to deployers                              | 13             | System card, instructions for use                                              |
| Human oversight designed into the system                               | 14             | HITL gateway (ADR-0011), autonomy levels (ADR-0015), escalation (ADR-0034)     |
| Accuracy, robustness and cybersecurity                                 | 15             | Model behavioural contracts (ADR-0051), abuse cases (ADR-0050), OWASP matrices |
| Provider obligations and quality management system                     | 16, 17         | The 15-phase lifecycle itself (ADR-0058) and its gates                         |
| Corrective actions and duty to inform                                  | 20             | AI incident runbook (#40), model rollback from the dependency manifest         |
| Conformity assessment, declaration, CE marking, registration           | 43, 47, 48, 49 | Adopter obligation; matrix carries the evidence pointers                       |
| Transparency toward people interacting with the system                 | 50             | System card, user-facing disclosure requirement                                |
| Post-market monitoring                                                 | 72             | `specs/compliance/ai-post-market-monitoring.md` (#27)                          |
| Serious-incident reporting                                             | 73             | AI incident runbook + reporting procedure (#27, #40)                           |

### 5. Application dates

Recorded per obligation in the control matrix. As verified on 2026-09-13, the timeline is:
Article 5 prohibitions from **2 February 2025**; general-purpose AI model obligations from
**2 August 2025**; Article 50 transparency and the governance and penalties regime from
**2 August 2026**; Annex III high-risk obligations (Art. 6(2)) from **2 December 2027**; Annex I
high-risk obligations (Art. 6(1)) from **2 August 2028**. These dates were amended after the
original publication of the Regulation, so each review of this ADR re-verifies them against the
consolidated text and records the verification date.

### 6. Re-classification triggers

The classification is re-assessed, and this ADR amended, whenever any of these occurs:

- a new `action_type` is registered in the dual-use registry (#39);
- the system is used in a new Annex III area, or in a new jurisdiction;
- the autonomy level is raised, or the HITL gateway is bypassed for any action class;
- the foundation model is replaced, or its provider changes its systemic-risk determination;
- the system begins to generate or manipulate content shown to people without disclosure;
- an Article 6(3) derogation is invoked, extended or withdrawn.

A re-classification that would *lower* obligations requires the same approval as the original
classification, plus a recorded rationale. Lowering by silence is prohibited.

## Consequences

### Positive

- Every obligation in the EU AI Act control matrix now traces to a recorded role and tier instead
  of to an unexplained table cell, which is what makes the matrix auditable.
- The default is conservative: high-risk unless narrowed with evidence, so an adopter cannot fall
  out of scope by omission.
- Article 5 is treated as a refusal condition rather than a risk to mitigate, which matches how
  the Phase 10 gate already behaves for other non-waivable controls.

### Negative / Trade-offs

- Assuming high-risk by default imposes the full Chapter III evidence burden on adopters whose use
  case may genuinely be out of scope until they document the Article 6(3) assessment.
- The role table is a per-adoption fact; an adopter that merely deploys someone else's agentic
  system inherits a different, smaller obligation set and must amend this ADR rather than follow
  it verbatim.
- Application dates were amended once and may be amended again; the corpus carries a date that is
  correct at review time, not a guarantee.

## Alternatives Considered

- **Keep the single asserted "High-Risk" cell.** Rejected: not auditable, not re-derivable, and
  silent about role, Article 50 and the GPAI regime.
- **Classify as minimal risk because a human approves every action.** Rejected: human oversight is
  a *requirement* for high-risk systems (Art. 14), not an exemption from the tier. Treating a
  control as a reason to drop the classification inverts the Regulation.
- **Leave classification entirely to the adopter.** Rejected: the corpus would then ship
  obligations with no stated trigger, which is how the previous version failed.
- **Assert that the corpus is out of scope because it contains no code.** Rejected as misleading:
  the corpus is the governance layer of a system that is in scope, and its artefacts are the
  evidence that system relies on.

## Compliance & Risk

- **Controls affected:** creates `specs/compliance/eu-ai-act-control-matrix.yaml` (#24); binds the
  Phase 10 AI Safety gate to Article 5 as a refusal condition.
- **Data classification impact:** none directly; Article 10 obligations flow to the data-governance
  package (#28, #33, #34).
- **Autonomy impact:** none. It records why the existing HITL and autonomy controls are mandatory,
  and adds re-classification triggers when autonomy changes.
- **Review/expiry:** reviewed at every re-classification trigger and at minimum annually; the
  application dates are re-verified at each review.

## Grounding

Article numbering, titles and the application timeline were verified on 2026-09-13 against the
published structure of Regulation (EU) 2024/1689. Where a source disagreed with another, the
article numbering that matches the Regulation's own chapter structure was used (Art. 9 risk
management, Art. 10 data and data governance, Art. 14 human oversight, Art. 50 transparency,
Art. 72 post-market monitoring, Art. 73 serious incidents). The full text of the Regulation is not
reproduced here; obligations are paraphrased, as the OWASP matrices already do for their standards.

---

## Related

- `specs/compliance/eu-ai-act-control-matrix.yaml` — the machine-verified obligation set
- `docs/ai-governance/eu-ai-act-compliance.md` — human-readable reading of the matrix
- `docs/compliance/iso42001-scope-and-soa.md` — the management-system side of the same programme
