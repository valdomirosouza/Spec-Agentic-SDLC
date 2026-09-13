<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0094 — Data Residency and Sovereignty

**Status:** Accepted
**Date:** 2026-09-13
**Authors:** DPO with Tech Lead (drafted with Claude Code)
**Spec:** `specs/privacy/training-data-governance.md` · `docs/privacy/data-processing-register.md`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0012](ADR-0012-pii-masking-strategy.md) (PII masking), [ADR-0013](ADR-0013-data-retention-policy.md) (retention), [ADR-0018](ADR-0018-db-encryption-at-rest.md) (encryption at rest), [ADR-0019](ADR-0019-redis-tls-value-encryption.md) (Redis TLS), [ADR-0093](ADR-0093-eu-ai-act-role-and-risk-classification.md) (EU AI Act role)

---

## Context

Data residency appeared in the corpus four times, and never as a decision. Three were the same
unanswered prompt in `docs/governance/control-applicability-matrix.md` — *"Where must data be
stored / may it leave a region?"* — and one was a value in `docs/dependency-manifest.yaml`
recording that the model provider runs in the US. An unanswered question in an applicability matrix
is worse than no question: it implies someone will answer it, and no one does.

Residency is not only a legal constraint. For an agentic system it is an **architectural** one,
because the most consequential cross-border transfer is invisible in the infrastructure diagram:
every prompt sent to a hosted model is a transfer of whatever is in that prompt, to wherever the
provider runs. A team can hold every database in one region and still transfer personal data
continuously.

Three forces pull against each other:

- **Legal.** GDPR Chapter V and LGPD Arts. 33–36 restrict transfers; some sectors and public
  customers require data to stay in a jurisdiction outright.
- **Operational.** The strongest models, and the managed services around them, are not available in
  every region. Pinning a region can mean accepting a weaker model or building more infrastructure.
- **Honest capability.** The corpus governs a template. It cannot declare a residency posture for
  every adopter, and declaring one it cannot enforce would be worse than declaring none.

## Decision

### 1. Residency is decided per data class, not per system

| Class    | Default residency                                                  | May leave the region?                                                              |
| -------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **L1** (direct identifiers, credentials, special-category) | **Primary region only** | **No.** Not in storage, not in a prompt, not in a log, not in a backup                |
| **L2** (indirect identifiers, personal content)            | Primary region          | Only under a valid transfer instrument, recorded per destination, and masked wherever masking preserves the purpose |
| **L3** (internal operational data, audit records)          | Primary region          | Yes, to a destination with an equivalent security posture, recorded in the processing register |
| **L4** (non-personal, aggregate, telemetry after redaction)| Unconstrained           | Yes                                                                                  |

The **primary region** is declared by the adopting organisation. This corpus does not choose one;
it requires the choice to be recorded and makes the unrecorded case a defect rather than a silence.

### 2. A prompt is a transfer

**Any personal data placed in a prompt, a tool argument, a retrieval result or an agent's memory is
transferred to wherever the model provider processes it.** This is the rule that changes behaviour:

- L1 data **never** reaches a model call. The PII filter is a residency control, not only a privacy
  one, and this ADR is a second reason it may not be weakened.
- L2 data reaches a model call only when the provider's processing region is covered by a valid
  transfer instrument recorded in `docs/privacy/data-processing-register.md`.
- The **model's processing region is a governed fact**, recorded in
  `docs/dependency-manifest.yaml` beside its version, and re-verified when the model is promoted.
  A model version change that moves processing to another region is a **residency change** and is
  approved as one, not as a dependency bump.

### 3. Sovereignty is separate from residency

Residency asks where data sits. **Sovereignty asks whose law reaches it.** Data held in-region by a
provider subject to a foreign disclosure regime is resident but not sovereign. Where a customer or
a regulator requires sovereignty rather than residency, the requirement is recorded as such in the
processing register, and the provider selection is constrained accordingly. Conflating the two
produces a posture that satisfies an architecture review and fails a customer's legal review.

### 4. What must be recorded, and where

| Fact                                                       | Recorded in                                              |
| ---------------------------------------------------------- | ---------------------------------------------------------- |
| The primary region                                         | The adopter's amendment to this ADR                       |
| Processing region of every third-party service and model   | `docs/dependency-manifest.yaml`                           |
| Transfer instrument per destination                        | `docs/privacy/data-processing-register.md`                |
| Sub-processors and their regions                           | `docs/privacy/sub-processor-register.md`                  |
| Per-dataset residency constraint, where stricter           | The dataset's row in `docs/data/data-catalog.md`          |
| Residency answer for the applicability matrix              | This ADR, referenced from the matrix                      |

### 5. Backups, logs and telemetry follow the data

The three places residency is most often lost. A backup replicated cross-region, a log shipped to a
provider in another region, and telemetry exported to a hosted collector are each transfers of
whatever they contain. Telemetry is L4 **only after** the collector redaction of ADR-0043 has run;
before that it is the class of its source.

### 6. Changes

A residency change — new region, new provider region, new transfer instrument, withdrawal of an
adequacy decision — requires: an update to this ADR, DPO approval, an update to the processing
register, and a re-assessment of any DPIA that relied on the previous position. **An adequacy
decision being struck down is a residency incident**, handled on the incident path rather than at
the next quarterly review.

## Consequences

### Positive

- The three open questions in the applicability matrix have an answer, and the answer names where
  each fact lives rather than restating it.
- Treating a prompt as a transfer closes the gap an infrastructure-only view leaves open, and gives
  the PII filter a second, independent reason to exist.
- Separating sovereignty from residency prevents a posture that passes internally and fails a
  customer's legal review.

### Negative / Trade-offs

- Pinning L1 and L2 to a primary region can exclude the strongest available model in some
  jurisdictions, and the corpus does not pretend otherwise.
- A model promotion now has a residency check, which slows promotion when the provider changes
  processing regions.
- The primary region itself is left to the adopter, so this ADR constrains without deciding — a
  deliberate limit of a template, not an omission.

## Alternatives Considered

- **Declare a primary region in the corpus.** Rejected: the corpus has no data and no jurisdiction;
  an adopter in another region would inherit a wrong default and might not notice.
- **Treat residency as an infrastructure concern only.** Rejected: it is the view under which
  prompts, logs, backups and telemetry leak, which is where it actually happens.
- **Require sovereignty everywhere.** Rejected as disproportionate: it would exclude most managed
  AI services for use cases that do not need it.
- **Leave the questions open, as before.** Rejected: an unanswered question in an applicability
  matrix reads as a commitment to answer it, and nothing was answering it.

## Compliance & Risk

- **Controls affected:** gives ADR-0012's PII filter a residency rationale; adds a residency check
  to model promotion (`docs/ai/model-lifecycle.md`); constrains `ART-10` and the processing register.
- **Data classification impact:** none to the classes themselves; residency obligations are now
  attached per class.
- **Autonomy impact:** none.
- **Review/expiry:** reviewed annually, on any change in §6, and whenever ADR-0093 is amended.

---

## Related

- `docs/privacy/data-processing-register.md` — transfer instruments per destination
- `docs/governance/control-applicability-matrix.md` — the questions this ADR answers
- [ADR-0043](ADR-0043-otel-collector-pii-redaction-tail-sampling.md) — when telemetry becomes L4
