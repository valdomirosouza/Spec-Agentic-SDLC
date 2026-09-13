---
id: SPEC-AI-020
kind: policy
status: approved
owner: Security Lead
issue: 41
governing_adrs:
  - ADR-0050
  - ADR-0036
  - ADR-0048
  - ADR-0093
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/ai/guardrails.md
  - specs/security/owasp-genai-control-matrix.yaml
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# AI red team programme

> **Owner:** Security Lead · **Co-owner:** AI Governance Lead
> **Satisfies:** EU AI Act `ART-15` · ISO/IEC 42001 A.6 · NIST AI RMF MEASURE 2
> **Feeds:** `tests/abuse_cases/` and the ratchet of ADR-0050

## 1. Why a programme rather than an exercise

The corpus asked for a red team in one line — "quarterly red-team exercise documented in
`docs/postmortems/`" — and no exercise had ever been recorded. A line in a spec produces nothing.
A programme with a scope, a cadence, rules of engagement and a defined destination for findings
produces tests.

**The destination is the point.** A red-team exercise whose findings live in a report is theatre.
Every finding here ends as an abuse case in the automated suite, where the ratchet of ADR-0050
guarantees the count never decreases — so the system cannot regress to a weakness that was already
demonstrated.

## 2. Scope

| In scope                                                       | Out of scope                                                       |
| -------------------------------------------------------------- | -------------------------------------------------------------------- |
| The agentic system: prompts, tools, memory, retrieval, guardrails, HITL routing | The model provider's infrastructure                        |
| The autonomy model and its feature flags                       | Third-party services beyond their integration boundary               |
| The retrieval corpus as an injection surface                   | Social engineering of employees (a separate exercise)                |
| The delivery agents and the harness hooks                      | Physical security                                                    |

**The two surfaces that matter most here** are the ones an ordinary application red team does not
have: the **retrieval corpus** (content the system trusts and an attacker may be able to write to)
and the **autonomy boundary** (the difference between proposing and doing).

## 3. Techniques

| # | Technique                          | The question it asks                                                              | OWASP LLM |
| - | ---------------------------------- | ----------------------------------------------------------------------------------- | --------- |
| 1 | **Direct prompt injection**        | Can user input override the system instruction?                                    | LLM01     |
| 2 | **Indirect prompt injection**      | Can a retrieved document, tool result or repository file issue instructions?        | LLM01     |
| 3 | **Jailbreak and role-play**        | Can the refusal behaviour be bypassed by framing?                                  | LLM01     |
| 4 | **Sensitive-information disclosure** | Can the system be made to reveal secrets, PII, or another tenant's context?       | LLM02     |
| 5 | **Memory poisoning**               | Can content be planted that influences a **later, different** session?             | LLM04     |
| 6 | **Tool abuse and confused deputy** | Can a registered tool be induced to act outside its intent, using the agent's authority? | LLM06 |
| 7 | **Autonomy escalation**            | Can an action be made to look low-risk enough to skip the gateway?                 | LLM08     |
| 8 | **Excessive agency chaining**      | Can several individually-permitted actions compose into a prohibited effect?        | LLM08     |
| 9 | **Output-handling exploitation**   | Can output reach a sink that executes or renders it unsafely?                       | LLM05     |
| 10 | **Denial of wallet**              | Can cost be driven up without an obvious failure?                                   | LLM10     |

**Techniques 5, 7 and 8 are the agentic ones.** They have no equivalent in a classic application
test, they are the hardest to automate, and two of them — memory poisoning and agency chaining —
are where the corpus's own controls are weakest: memory governance controls are documented and not
yet implemented, and no control examines a *sequence* of permitted actions.

## 4. Rules of engagement

| Rule                                                             | Reason                                                              |
| ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| Non-production environments only, unless production is authorised in writing | A successful exercise executes real actions          |
| No real personal data; synthetic markers only                    | Constitution Art. III applies to the red team too                    |
| Planted content is tagged and removed after the exercise         | An untracked injection payload becomes a live vulnerability          |
| Every attempt is logged with timestamp and operator              | Distinguishes exercise traffic from a real attack in the audit trail |
| SRE notified before and after                                    | Otherwise the exercise triggers a real incident response             |
| A **real** vulnerability found is reported immediately, not at the end | Severity does not wait for the report                       |
| Findings are embargoed until mitigated or accepted               | Standard disclosure discipline, internally too                       |

**The tagging rule has bitten every team that skipped it.** An injection payload planted in a
corpus and forgotten is indistinguishable from an attack, and it keeps working.

## 5. Cadence

| Trigger                                    | Scope                                                          | Who                                  |
| ------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------- |
| **Quarterly**                              | Full technique list against the current system                  | Security Lead + AI Governance Lead    |
| **Before raising autonomy** to a new level | Techniques 6, 7 and 8 against the newly permitted action classes | Security Lead — **blocking**          |
| **On registering a new action type**       | Techniques 6 and 7 against that type                            | Security Lead — before activation     |
| **On a model change**                      | Techniques 1, 3 and 4 — refusal behaviour is version-specific   | AI Governance Lead                    |
| **After an AI incident**                   | The technique class involved                                    | Whoever ran the postmortem            |

The autonomy row is the one with teeth: **an autonomy increase does not ship without an exercise**,
which makes this programme a gate rather than an activity.

## 6. Findings

| Severity     | Definition                                                             | Destination                                                                 |
| ------------ | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| **Critical** | Guardrail bypassed with real-world effect, or approval circumvented      | Incident path (`RB-AI-001`); fix before the exercise closes; abuse case       |
| **High**     | Guardrail bypassed, effect contained by a later control                  | Fix within the cycle; abuse case                                              |
| **Medium**   | Degraded behaviour without bypass                                        | Backlog with an owner; abuse case                                             |
| **Low**      | Observation, no demonstrated bypass                                      | Recorded; abuse case only if cheaply expressible                              |

**Every Critical, High and Medium finding becomes an abuse case.** A finding that cannot be
expressed as a test is recorded as such **with the reason**, because "we could not automate it" is
itself a fact worth keeping — it names where the ratchet does not protect us.

## 7. Exercise record

| Field                | Content                                                          |
| -------------------- | ------------------------------------------------------------------ |
| Date and operators   |                                                                    |
| Scope and techniques | Which of the ten, and why the others were excluded                |
| Environment          | And the authorisation, if production                              |
| Attempts             | Count per technique, and the outcome of each                      |
| Findings             | Severity, description, evidence reference                         |
| Abuse cases added    | Test ids, and the resulting ratchet count                         |
| Not automatable      | Findings that could not become tests, with the reason             |
| Controls confirmed   | **What held** — as important as what broke                        |

The "controls confirmed" row exists because an exercise that finds nothing still produces
evidence, and an exercise recorded only when it fails makes the control history look worse than it is.

## 8. Exercise log

| Date | Scope | Findings (C/H/M/L) | Abuse cases added | Report |
| ---- | ----- | ------------------ | ----------------- | ------ |
| *No exercise has been conducted.* The first is due at the next quarterly cycle. | | | | |

Recording the empty state is deliberate: the previous one-line mention implied a quarterly exercise
was happening, and none was.

## 9. What is enforced today

| Obligation                                    | Enforcement                                                |
| --------------------------------------------- | ------------------------------------------------------------ |
| Abuse-case count never decreases              | Test-integrity gate (ADR-0050, ADR-0065) — blocking         |
| Exercise before an autonomy increase          | **Review only** — governance sign-off (ADR-0015)            |
| Exercise before activating an action type     | **Review only** — Phase 10 gate                             |
| Quarterly cadence                             | **Review only** — council agenda                            |

## 10. Open items

| # | Item                                                        | Owner              | Resolve by            |
| - | ------------------------------------------------------------- | ------------------ | --------------------- |
| 1 | First exercise conducted and logged                          | Security Lead      | Next quarterly cycle  |
| 2 | Memory-poisoning technique blocked on unimplemented controls | AI Governance Lead | With memory governance |
| 3 | A control that examines action **sequences**, not only single actions | AI Governance Lead | Next quarterly review |

## Related

- [`guardrails.md`](guardrails.md) — the controls under test
- [`../security/owasp-genai-control-matrix.yaml`](../security/owasp-genai-control-matrix.yaml) — the mapping each technique probes
- [`../../docs/ai-governance/dual-use-registry.md`](../../docs/ai-governance/dual-use-registry.md) — what each action type can do
- [`../../docs/runbooks/RB-AI-001-ai-incident.md`](../../docs/runbooks/RB-AI-001-ai-incident.md) — when a finding is live
