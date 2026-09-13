<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# System card — the agentic delivery system

> **Owner:** AI Governance Lead · **Version:** 1.0 · **Date:** 2026-09-13
> **Satisfies:** EU AI Act `ART-11` and Annex IV, `ART-13` (information to deployers) and `ART-50`
> (transparency) · ISO/IEC 42001 A.8 · NIST AI RMF MAP 1 and MAP 2
> **Model card:** [`model-card.md`](model-card.md) · **Classification:** [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md)

A model card describes a model. This card describes the **system** the model sits inside: what it
is for, what it can and cannot do, who oversees it, and what it is not permitted to be used for.
For a system whose risk comes from *composition* — a model plus tools plus memory plus autonomy —
the model card alone is the wrong unit of description.

## 1. What this system is

An agentic software-delivery system that reads specifications, proposes work, drafts artefacts and
executes actions in a software repository **under mandatory human supervision**. It sits inside a
15-phase lifecycle in which thirteen phases block and nine of them require a named human
(phases 2, 4, 5, 7, 10, 11, 12, 13, 14); the other four block on machine criteria.

| Property                | Value                                                                      |
| ----------------------- | ---------------------------------------------------------------------------- |
| Purpose                 | Turn approved specifications into reviewed, traceable changes               |
| Deployment              | Developer workstations and CI, inside the adopting organisation             |
| Users                   | Engineers, and the reviewers who hold the gates                             |
| Affected parties        | Anyone whose data the delivered software processes                          |
| Risk classification     | High-risk by default under Art. 6(2), narrowable only by documented assessment |
| Autonomy default        | `NONE` — every consequential action requires an approval                    |

## 2. Components and boundaries

| Component            | Role                                                        | Boundary                                                       |
| -------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------- |
| Foundation model     | Reasoning and drafting                                       | Third party; deployer relationship; L1 never reaches it          |
| Agents               | Perceive, reason, propose                                     | Cannot execute a real-world action directly                     |
| HITL gateway         | Holds every real-world action for a named human               | The system's load-bearing control                                |
| Guardrails           | PII filter, prompt-injection guard, output sanitiser, action limits | Run on every call, never disabled                        |
| Tool registry        | What an agent may invoke                                      | Zero-trust: not listed means not callable                       |
| Memory and retrieval | Durable context                                               | L2, encrypted at rest, not cleared for model training           |
| Autonomy flags       | Standing permission per action class                          | Changed only under governance review                            |
| Harness hooks        | Deny push, merge, release, deploy to subagents; block unapproved specs | Enforced by the harness, not by the prompt              |

**Where the system ends.** It proposes and drafts. It does not merge, deploy, release, approve its
own specification, or change its own autonomy. Those five are reserved to humans and enforced
outside the model's reach.

## 3. What it can do

- Draft specifications, plans, task lists, ADRs, tests and code against an approved specification.
- Analyse consistency across artefacts and report gaps without editing them.
- Execute a task list phase by phase, tests first, stopping at every gate.
- Run and report validation, and escalate rather than resolve a conflict with a binding decision.

## 4. What it cannot do, by construction

| Cannot                                          | Prevented by                                                   |
| ----------------------------------------------- | ---------------------------------------------------------------- |
| Execute a real-world action without approval    | HITL gateway; autonomy defaults to `NONE`                       |
| Push, merge, release or deploy from a subagent  | `PreToolUse` high-risk-action guard — denies, does not ask      |
| Start code work on an unapproved specification  | `UserPromptSubmit` sdd-gate — blocks the prompt (ADR-0092)      |
| Call a tool that is not registered              | Zero-trust tool registry (ADR-0048)                             |
| Weaken a guardrail or a protected constitutional article | Constitution; check-corpus invariants; dual approval    |
| Reduce the abuse-case count                     | Test-integrity ratchet (ADR-0050, ADR-0065)                     |

## 5. Human oversight

| Question                                   | Answer                                                                  |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| Who oversees?                              | The named reviewer at each of the nine human gates; the approver at the HITL gateway |
| Can a human decide not to use the output?  | Yes — rejection is a first-class outcome, and expiry rejects by default   |
| Can a human reverse an executed action?    | Through the ordinary change path; irreversible actions require approval before execution, not after |
| Can a human stop the system?               | Yes — autonomy to `NONE`, or disable the action type                     |
| How is automation bias countered?          | Approval latency and override rate are monitored as leading indicators (`ART-72` plan §2) |

The last row is the one most systems omit. Oversight that has degraded into rubber-stamping is
still oversight on paper, and the monitoring plan treats falling approval latency alongside a
falling override rate as a signal in its own right.

## 6. Transparency (Art. 50)

- People interacting with the system are told they are interacting with an AI system.
- Artefacts the system drafts carry a marker that they were agent-generated and require human
  review before approval.
- The system does not generate synthetic media, perform emotion recognition or biometric
  categorisation. Should an adopter add any of these, Art. 50's marking obligations attach and this
  card must be updated before that use begins.

## 7. Risks and residual risk

| Risk                                                    | Mitigation                                                  | Residual                                                        |
| ------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------- |
| Fabricated API, path or decision reaching an artefact   | Constitution Art. IX; groundedness SLI; evaluator; review     | Real — a plausible fabrication can pass review                   |
| Prompt injection through retrieved or supplied content  | Injection guard; output sanitiser; tool registry              | Real — mitigated, not eliminated                                 |
| Automation bias in the approver                         | Monitoring of latency and override rate                       | Real — detected after the fact                                   |
| Memory poisoning                                        | Memory governance controls are **target controls, not yet implemented** | High — stated plainly rather than implied            |
| Model behaviour change without a version change         | Contract suite at promotion; post-market monitoring           | Real between monitoring cycles                                   |
| Personal data reaching the model                        | PII filter; L1 never; residency rule                          | Depends on filter coverage of the adopter's fields               |

**Residual risk is not zero and this card does not claim it is.** Four of the six rows remain real
after mitigation, and the memory-poisoning row is worse than the others because its controls are
documented and not yet built.

## 8. Data

| Dataset                | Role                               | Class | Cleared for model use?                            |
| ---------------------- | ------------------------------------ | ----- | --------------------------------------------------- |
| Retrieval and memory corpus | Grounding and session memory   | L2    | **No** — datasheet is draft with six unresolved rows |
| Audit trail            | Evidence                             | L3    | No — immutable evidence, never an input             |
| Telemetry              | Monitoring                           | L4 after redaction | No                                     |

No dataset is used to train or fine-tune any model
(`specs/privacy/training-data-governance.md`).

## 9. Monitoring and incidents

Post-market monitoring runs on the plan in
`specs/compliance/ai-post-market-monitoring.md`; incidents follow
[`../runbooks/RB-AI-001-ai-incident.md`](../runbooks/RB-AI-001-ai-incident.md) and, where serious, the Art. 73 procedure. A model version
is rolled back by re-pinning it in the dependency manifest.

## 10. Contact and reporting

Concerns about an agent action, an output, or this card are raised through the channel in
`skills/ethics/ethical-ai-review.md`. **The adopting organisation fills in the published point of
contact** required by Art. 50 and ISO/IEC 42001 A.8; it is deliberately not invented here.

## 11. Version history

| Version | Date       | Change                                                    |
| ------- | ---------- | ----------------------------------------------------------- |
| 1.0     | 2026-09-13 | Created. First system-level description of the agentic system (#38) |

## Related

- [`model-card.md`](model-card.md) · [`model-registry.md`](model-registry.md) · [`autonomy-boundaries.md`](autonomy-boundaries.md)
- [`eu-ai-act-compliance.md`](eu-ai-act-compliance.md) — the obligations this card evidences
- [ADR-0093](../adr/ADR-0093-eu-ai-act-role-and-risk-classification.md) · [ADR-0092](../adr/ADR-0092-command-lifecycle-hooks-vs-claude-code-hooks.md)
