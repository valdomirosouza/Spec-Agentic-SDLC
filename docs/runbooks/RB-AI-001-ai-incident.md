<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# RB-AI-001 — AI Incident: jailbreak, harmful output, hallucination in production, model rollback

**Owner:** SRE Lead + AI Governance Lead
**Severity scope:** P0 (harm occurred or an unapproved irreversible action executed), P1 (guardrail bypassed, no harm yet), P2 (degraded output quality)
**Last updated:** 2026-09-13
**Satisfies:** EU AI Act `ART-20` and `ART-73` · `specs/compliance/ai-post-market-monitoring.md` §5

---

## Overview

The corpus had six runbooks, none of which covered an incident caused by the model itself. The
existing HITL recovery runbook covers the gateway failing; this one covers the gateway holding
while the thing behind it behaves wrongly.

**The distinction that drives every decision below:** an availability incident is over when the
service returns. An AI incident is over when you know **what was produced, what consumed it, and
whether any of it had effect**. Restoring service without answering those three leaves the harm in
place.

---

## Severity

| Severity | Condition                                                                                  | First action                               |
| -------- | -------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **P0**   | Harm to a person or property occurred, **or** an irreversible action executed without the required approval | Contain immediately, then §6 serious-incident path |
| **P1**   | A guardrail was bypassed, or a harmful output reached a human, with no effect yet           | Contain, preserve evidence, investigate     |
| **P2**   | Output quality degraded: groundedness below target, evaluator failing, contract test failing | Lower autonomy, investigate before rollback |

**A near miss that only a human gate stopped is treated as P1 at minimum.** The gate working is
evidence the gate is load-bearing, not evidence the system is safe.

---

## 1. Containment — the four levers, in order of blast radius

Apply the smallest lever that stops the bleeding. Each is independent; more than one may apply.

| # | Lever                         | What it stops                                   | How                                                                  | Reversible |
| - | ----------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------- | ---------- |
| 1 | **Disable the action type**   | One capability                                  | Remove it from the tool registry; unregistered means uncallable (ADR-0048) | Yes    |
| 2 | **Lower the autonomy level**  | All autonomous execution in a class             | Set the autonomy flag down, `NONE` stops everything autonomous       | Yes        |
| 3 | **Roll back the model**       | Behaviour introduced by a version               | Re-pin `llm_model` in `docs/dependency-manifest.yaml`, redeploy       | Yes        |
| 4 | **Stop the agent service**    | Everything                                      | Scale to zero                                                        | Yes        |

**Lever 2 before lever 3.** Lowering autonomy takes effect immediately and keeps the system useful
under human approval; a model rollback takes a deploy and may not be the cause. Reaching for the
rollback first is the common mistake, and it destroys the evidence of what the current version was
doing.

**Do not clear agent memory as a containment step.** If poisoning is suspected, memory is the
evidence. Isolate the session and preserve it (§2).

---

## 2. Preserve evidence — before anything else is changed

| Artefact                    | Where                                                   | Why it disappears                            |
| --------------------------- | --------------------------------------------------------- | ---------------------------------------------- |
| The exact prompt and output | Agent spans, `llm.inference` (ADR-0044, ADR-0045)        | Trace sampling and retention windows          |
| Guardrail decisions         | Guardrail events and audit trail                          | Log retention                                  |
| The approval record         | HITL store and archive                                    | TTL on the live store                          |
| Retrieval results used      | Retrieval span attributes                                 | Not retained by default                       |
| Model version and config    | `docs/dependency-manifest.yaml` at that commit            | Overwritten by the rollback in §1              |
| Memory state                | Session memory for the affected session                   | Overwritten by later sessions                  |

**Record the commit SHA and the model version before rolling back.** Both are the answer to
"what was running", and both are the first things a rollback changes.

---

## 3. Scenario — prompt injection or jailbreak

**Symptom:** The agent performed, or proposed, something outside its instructions; or guardrail
interventions spiked with no release to explain them.

1. Contain with lever 1 on the abused action type, or lever 2 if the vector is unclear.
2. Identify the injection vector: user input, a retrieved document, a tool result, or agent memory.
3. **If the vector is a retrieved document or memory, treat the corpus as compromised** until the
   document is found. Other sessions retrieving the same document are affected.
4. Check the audit trail for other actions from the same session and the same document.
5. Add the case to `tests/abuse_cases/` before closing. The ratchet never decreases (ADR-0050).
6. If the guard did not fire, it is a guardrail defect: Security Lead review, and a
   `src/guardrails/` change needs dual approval.

---

## 4. Scenario — harmful or non-compliant output

**Symptom:** Output that is offensive, discriminatory, exposes personal data, or implements a
practice prohibited under EU AI Act Art. 5.

1. Contain with lever 1; if the output reached a person, this is **P0 or P1, not P2**.
2. Determine reach: was it shown to a user, sent externally, written to a durable artefact?
3. **If personal data was exposed:** notify the DPO immediately. The 72-hour breach clock may be
   running, and it is not the same clock as the Art. 73 clock in §6.
4. **If an Art. 5 practice was implemented**, even inadvertently: AI Governance Lead, immediate
   escalation, and the capability stays disabled until an ADR records how recurrence is prevented.
5. Ethical-violation procedure in `skills/ethics/ethical-ai-review.md` applies alongside this one.

---

## 5. Scenario — hallucination reaching a decision

**Symptom:** An artefact cites an API, a path, a decision or a number that does not exist, and it
passed review.

1. **Do not contain first — scope first.** A single fabrication is a defect; a pattern is an
   incident. Check the groundedness series before escalating.
2. Find everything the same session produced. Fabrications cluster.
3. If the fabrication reached merged work, treat it as a correctness incident on the normal path,
   with the additional question: **why did review not catch it?**
4. If groundedness is below its target (ADR-0080), it is a model incident: §7.
5. The Constitution IX violation is in the artefact, not only in the model. Correct both.

---

## 6. Scenario — unapproved irreversible action executed

**This is the most serious case in this runbook**, because the control the whole risk
classification depends on has failed.

1. Contain with lever 4. Stop the service, not just the capability.
2. Notify: AI Governance Lead, Security Lead, Tech Lead. Immediately, not at the next standup.
3. Establish and **record the timestamp** at which the causal link was established. Every Art. 73
   deadline is measured from it (`specs/compliance/ai-post-market-monitoring.md` §5.2).
4. Determine why the gateway did not hold: bypassed, misconfigured, or the action type not
   classified as requiring approval.
5. Attempt a compensating action if the effect is reversible; log the attempt and its outcome.
6. Classify as a serious incident unless the AI Governance Lead determines otherwise, and record
   that determination either way.
7. The service does not return until the gateway failure has a test that would have caught it.

---

## 7. Scenario — model behaviour change or contract failure

**Symptom:** The model contract suite fails on a version that previously passed, or evaluator
scores shift with no change on our side.

1. Re-run the contract suite to confirm it is not flaky.
2. Lower autonomy (lever 2) while investigating. Do not roll back yet.
3. Compare against the provider's published changes. A silent server-side change is the usual cause.
4. If confirmed: roll back with lever 3 by re-pinning the previous version, and record the
   BLOCKED verdict for the failing version in the manifest with its evidence, exactly as the
   existing candidate entry does.
5. A failing contract test is a finding. **Never loosen the test to make the version promotable.**

---

## 8. Recovery criteria

The incident is not closed until all of these are true:

- [ ] The cause is identified, or the investigation's limit is documented
- [ ] Evidence in §2 is preserved and referenced from the incident record
- [ ] Blast radius is known: what was produced, what consumed it, what had effect
- [ ] Containment is lifted deliberately, with the reason recorded
- [ ] A test exists that would have caught it — abuse case, contract test, or guardrail test
- [ ] Where personal data was involved, the DPO has closed their side
- [ ] Where it was serious, the Art. 73 report was filed and the record kept
- [ ] Postmortem completed within 48 hours (`docs/postmortems/POSTMORTEM-TEMPLATE.md`)

---

## 9. What this runbook does not cover

- HITL gateway unavailability — `RB-003-hitl-recovery.md`
- Store, broker or authentication failures — RB-004, RB-005, RB-006
- Ordinary rollback mechanics — `rollback-procedure.md`

---

## Related

- [`../../specs/compliance/ai-post-market-monitoring.md`](../../specs/compliance/ai-post-market-monitoring.md) — thresholds and the Art. 73 procedure
- [`../ai/model-lifecycle.md`](../ai/model-lifecycle.md) — promotion and rollback
- [`../ai-governance/dual-use-registry.md`](../ai-governance/dual-use-registry.md) — what each action type can do
- [`../../skills/ethics/ethical-ai-review.md`](../../skills/ethics/ethical-ai-review.md) — the ethical-violation path
