<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0104 — Dev-time Judge and Advisor Roles, and the Judge's Independence

**Status:** Accepted (2026-11-16, Tech Lead)
**Date:** 2026-11-15
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** `specs/features/SPEC-SDLC-002-judge-advisor-roles/spec.md`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0035](ADR-0035-ai-assisted-ci-review.md) (amended by this ADR), [ADR-0011](ADR-0011-hitl-hotl-model.md) (human oversight), [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation), [ADR-0058](ADR-0058-agentic-spec-driven-delivery-workflow.md) (delivery workflow), [ADR-0060](ADR-0060-task-atomicity-skill-budget.md) (skill budget), [ADR-0070](ADR-0070-governance-gate-enforcement-lifecycle.md) (report mode), [ADR-0080](ADR-0080-groundedness-scoring-as-an-sli.md) (groundedness), [ADR-0095](ADR-0095-single-delivery-entrypoint-and-the-branch-exception.md) (delivery entrypoint)

---

## Context

The runtime side of the corpus already judges agent output before it acts. The harness
`EvaluatorAgent` scores output and escalates after `harness_max_iterations` (SPEC-AI-008), and
HITL or HOTL is chosen by risk score (SPEC-AI-009). The dev-time delivery lifecycle driven by
`asdd-orchestrator` (ADR-0058, ADR-0095) has no equivalent:

- **The producer checks its own work before the gate.** The Phase 7 agent opens the PR, verifies
  the Definition of Done and requests review (`.claude/agents/asdd-phase-7-code-review.md`). The
  human reviewer is the first independent check.
- **There is nothing between proceeding and escalating.** A delivery agent that is unsure either
  carries on or stops with `[HITL-ESCALATE]` (CLAUDE.md §14, ADR-0034).
- **Reviewer and producer share a model.** ADR-0035 pins the CI AI review to "the active session
  model for consistency". A reviewer on the producer's model can share the producer's blind spots.

SPEC-SDLC-002 (approved 2026-11-15, #200, #201) specifies two roles to close these gaps. Its new-ADR
slug is `judge-advisor-roles-and-judge-independence`. Three of its assumptions resolve at this
phase: where the rubric comes from (A2), where the records live (A3) and how a timeout is set
(A4). A fourth, A5, says this ADR amends ADR-0035's model clause rather than superseding it.

The constraints are fixed elsewhere:

- The nine human gates and every `required_approvals` entry stay as they are (Constitution V).
- A new gate enters in report mode and is promoted under ADR-0070.
- Each task loads at most two skills (ADR-0060).

## Decision

We will add two dev-time delivery subagents under `.claude/agents/`. Both are invoked by
`asdd-orchestrator`, neither changes a gate, and the Judge is kept independent of the agent whose
work it judges.

### 1. The Judge (`asdd-judge`) gives a verdict and never approves

- The orchestrator invokes the Judge after a phase in its scope hands off with `human_gate: true`,
  and only once that phase's `ci_checks` in `docs/process/gates/phase-gates.yaml` are green. If the
  checks are red, the Judge does not run and the phase is blocked as before.
- The Judge returns one `judge_verdict_v1` record (spec §Key Entities): `pass`, `fail` or
  `escalate`, findings with evidence, the criteria it could not confirm, a groundedness score in
  the ADR-0080 sense, and both model ids. A criterion it cannot confirm makes the verdict not
  `pass`. A rubric or spec that cannot judge a criterion makes it `escalate`. It never invents a
  criterion.
- The Judge is read-only. It writes its own verdict and nothing else.
- No verdict satisfies a `required_approvals` entry or a human gate. The gate is always presented
  to the human. A missing verdict (error or timeout) is recorded as missing and never read as
  `pass`. A human who approves a gate whose verdict was `fail` records a one-line rationale.
- **Scope and mode.** Phase 7 only, in report mode: the verdict is attached to the gate and
  recorded, and routing does not change because of it. The Judge gets an entry in
  `docs/governance/gate-lifecycle.md`. Promotion to blocking, and any further phase, is a later
  `normal-change` under ADR-0070, one phase at a time, each with its own rubric.

### 2. The Judge is independent of the producer

- **Its own invocation, in isolated context.** It is never the producing phase's session and never
  the same invocation as an Advisor.
- **An allow-listed input envelope.** The envelope holds the phase's artefacts, the spec sections
  in scope and the phase rubric at a stated version. It excludes the producer's handoff `notes`,
  the producer's session and reasoning, the orchestrator's history and any Advisor output. The
  envelope is recorded with the verdict, so a reviewer can check what the Judge saw.
- **Model.** A different model class from the producer is recommended, not required. Both
  `judge_model` and `producer_model` are always recorded. When they are the same, the verdict says
  so. An adopter with a single approved model can comply.

### 3. The Advisor (`asdd-advisor`) recommends and the caller decides

- The Advisor is consulted on exactly two triggers. One is a phase that returned `blocked` and is
  about to be retried. The other is the implement ↔ converge loop entering its second round
  (`/sdd-converge`, bounded at three rounds).
- It returns one advice record: the question, the options, a recommendation and its rationale. The
  caller records whether it followed the advice and, if not, why.
- The Advisor is read-only. It never clears a gate, never satisfies an approval and never replaces
  a §14.1 escalation. When a §14.1 trigger has fired, `[HITL-ESCALATE]` is emitted whatever the
  advice says. Advice to skip or weaken a gate, test or guardrail is recorded and not acted on.

### 4. Where the rubric and the records come from (A2, A3, A4)

- **The rubric (A2).** The Phase 7 rubric has no criteria of its own. It is built from the spec's
  acceptance criteria and the Phase 7 `exit_criteria` in `phase-gates.yaml`. It is versioned, and
  each verdict names the version it used. The rubric's file location is set in the plan.
- **The records (A3).** Verdicts, input envelopes and advice records go in the per-run delivery
  state under `.agent/delivery/<feature_id>/`. That state is gitignored and written by
  `scripts/python/asdd_state.py`. A run's records are summarised in its committed FINAL-REPORT.
- **The timeout (A4).** The Judge has a fixed wall-clock limit, whose value is set in the plan.
  Reaching it is the missing-verdict case in §1.

### Amendment to ADR-0035

ADR-0035 pins the CI AI review's model to the producing session's model "for consistency". That
reason does not carry over to the Judge, whose value depends on not sharing the producer's view.
For the Judge, §2 applies. ADR-0035 is amended, not superseded. Its CI review workflow, model pin
and promotion path are unchanged by this ADR. A note at the top of ADR-0035 points here.

## Consequences

### Positive

- Every Phase 7 gate reached in report mode carries a verdict, or a recorded missing verdict. Every
  verdict names the criteria it checked and the ones it could not confirm. The reviewer sees where
  to look first.
- Independence can be audited. The recorded envelope and both model ids show what the Judge saw
  and which model judged.
- Retries and extra converge rounds get a second opinion first. The advice and whether it was
  followed are on the record.
- Report mode lets the corpus measure the Judge before anything depends on it. The measurement is
  calibration, proposal P6, which gets its own spec.

### Negative / Trade-offs

- **Automation bias.** A `pass` can lead a reviewer to look less closely. This ADR keeps the gate
  but cannot keep the reviewer's attention. Measuring that is P6, and risk-graduated review depth
  (P5) must wait for that data.
- **The artefact is untrusted input to its judge.** The producer writes the artefact, so it can be
  written to persuade the Judge (OWASP LLM01). §2 closes the other channels but not this one. The
  threat-model entry for it is a separate Phase 5 artefact.
- **Same blind spots remain possible.** A different model is only recommended, so a single-model
  adopter gets a Judge on the producer's model. The record makes this visible but does not prevent
  it.
- **Cost.** There is one more model invocation per Phase 7 gate, plus one per advised retry or
  round. Wall-clock and model are recorded per verdict so the cost can be read.
- **Two more agents** against Constitution VIII. The plan's Complexity Tracking table justifies
  them (spec Q1).

### Neutral

- The runtime `EvaluatorAgent` (SPEC-AI-008) and the CI AI review (ADR-0035) are unchanged.
- No human gate is added, removed or converted.

## Alternatives Considered

- **Do nothing.** The human stays the first independent check at Phase 7, and the producer keeps
  checking its own work. Rejected, because this is the gap the spec was approved to close.
- **Fold judging into `/sdd-analyze` and `/sdd-converge`.** This needs no new agent. Rejected
  (spec Q1): those commands run beside the producer's session, so the judgement would share its
  context, which is what independence is meant to exclude.
- **Require a different model class.** Rejected (spec Q2): it would exclude adopters with one
  approved model. Recording both models and flagging the overlap gives the reviewer the same
  information without that cost.
- **Supersede ADR-0035.** Rejected (A5): its CI review decision still stands. Only the reason given
  for its model choice fails to extend to a judge.
- **Enter in blocking mode.** Rejected: ADR-0070 requires report mode first, and a Judge that has
  never been calibrated should not block a merge.
- **Let the Advisor resolve a §14.1 trigger.** Rejected: a §14.1 escalation is a human decision by
  definition (ADR-0034), and advice is not a decision.

## Compliance & Risk

- **Controls affected:**
  - OWASP LLM01, because the Judge reads artefacts another agent wrote.
  - OWASP LLM09, because a verdict is advisory and a human decides.
  - Whether these need new rows in `specs/security/owasp-genai-control-matrix.yaml` is
    `uncertain — verify`. The matrix maps runtime controls, and these agents are dev-time. This is
    decided together with the threat-model entry.
- **Data classification impact:** none. Verdicts and advice cite paths, lines and test names, not
  data values (spec NFR-01).
- **Autonomy impact:** none. No feature flag and no autonomy level changes. No gate or approval is
  cleared by an agent (ADR-0011, ADR-0015).
- **Review/expiry:** revisit when the Judge's burn-in under ADR-0070 completes, or before it is
  extended beyond Phase 7.

---

## Related

- `specs/features/SPEC-SDLC-002-judge-advisor-roles/spec.md` — the requirements this ADR decides
- `docs/governance/gate-lifecycle.md` — report-mode registry the Judge enters
- `docs/adr/README.md` — master index & lifecycle definition
- `docs/adr/adr-review-checklist.md` — checklist to apply before marking this ADR `Accepted`
