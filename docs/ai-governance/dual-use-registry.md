# Dual-Use Risk Assessment Registry

**Owner:** AI Governance Lead
**Updated:** 2026-09-13
**Process:** `specs/ethics/ethical-ai-principles.md §4`

Every new `action_type` registered in the agent registry must have an entry here before
activation. Entries are append-only — supersede rather than delete when re-assessed.

**Entry rule.** An `action_type` with no entry here is **not activatable**, whatever the autonomy
level or the risk score permits. The Phase 10 AI Safety gate checks this registry, and an agent
proposing an unregistered action type is blocked by the zero-trust tool registry (ADR-0048) before
the question of approval arises.

**Answering `yes` is not a failure.** Several entries below answer `yes` to a dual-use question and
are still approved, because the mitigation bounds the consequence. What is refused is an
unmitigated `yes`, or an entry whose mitigation is the model's own behaviour rather than a control
outside it.

---

## Registry Format

```yaml
- action_type: <name>
  assessed_by: <name, role>
  assessment_date: <YYYY-MM-DD>
  dual_use_risks:
    - question: D-01 # enumerate/probe/attack external systems
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX # if mitigation is governed by an ADR
    - question: D-02 # generate/execute/transmit code without human review
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX
    - question: D-03 # access credentials/keys/tokens
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX
    - question: D-04 # scrape/exfiltrate/aggregate PII at scale
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX
    - question: D-05 # outbound HTTP to user-controlled URLs
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX
    - question: D-06 # harm to third parties if misused
      answer: yes | no
      mitigation: <description if yes>
      adr_reference: ADR-XXXX
  approved: true | false
  approval_notes: <optional rationale or conditions>
```

---

## Registered Action Types

Seven entries, one per always-HITL category in `specs/ai/hitl-hotl.md`. These are the categories
the specification already defines; an adopter registers its own concrete action types the same way.

```yaml
- action_type: external_data_exfiltration
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01 # enumerate/probe/attack external systems
      answer: no
      mitigation: Outbound calls restricted to the allow-list; no enumeration primitive is registered
      adr_reference: ADR-0048
    - question: D-02 # generate/execute/transmit code without human review
      answer: no
      mitigation: n/a — this category transmits data, not code
    - question: D-03 # access credentials/keys/tokens
      answer: no
      mitigation: Credentials are not in the agent's context; secrets access is a separate action type
    - question: D-04 # scrape/exfiltrate/aggregate PII at scale
      answer: yes
      mitigation: >-
        The defining risk of this category. Mandatory HITL regardless of risk score; PII filter
        before any egress; bulk threshold (entity_count > 100) is itself a mandatory-HITL trigger;
        L1 data never leaves the primary region.
      adr_reference: ADR-0012
    - question: D-05 # outbound HTTP to user-controlled URLs
      answer: yes
      mitigation: URL allow-list at every outbound boundary; metadata and link-local ranges blocked
      adr_reference: ADR-0093
    - question: D-06 # harm to third parties if misused
      answer: yes
      mitigation: Mandatory HITL; immutable audit of every egress; residency rule per data class
      adr_reference: ADR-0094
  approved: true
  approval_notes: >-
    Approved only under mandatory HITL. This action type may never be moved to HOTL by an autonomy
    level; doing so would require a new ADR and full governance sign-off.

- action_type: financial_transaction
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: No discovery or probing primitive is registered for payment systems
    - question: D-02
      answer: no
      mitigation: n/a
    - question: D-03
      answer: yes
      mitigation: Payment credentials held by the executing service, never in agent context; the agent proposes, the service holds
      adr_reference: ADR-0008
    - question: D-04
      answer: no
      mitigation: Transaction metadata is L2 and masked; no bulk aggregation path exists
    - question: D-05
      answer: no
      mitigation: Destination is a registered processor, never a user-supplied URL
    - question: D-06
      answer: yes
      mitigation: Irreversible and monetary. Mandatory HITL with reason text; per-action limits; immutable audit
      adr_reference: ADR-0011
  approved: true
  approval_notes: >-
    Irreversibility is the governing property, not the amount. A small transaction is as
    irreversible as a large one and carries the same mandatory approval.

- action_type: external_account_modification
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: Operates on a known account reference, not on a discovered one
    - question: D-02
      answer: no
      mitigation: n/a
    - question: D-03
      answer: yes
      mitigation: Modifying an account can change access. Mandatory HITL; the approver sees the before and after state
      adr_reference: ADR-0011
    - question: D-04
      answer: no
      mitigation: Single-account scope; bulk modification is a separate, unregistered capability
    - question: D-05
      answer: no
      mitigation: Provider endpoint from the allow-list
    - question: D-06
      answer: yes
      mitigation: Direct user impact. Mandatory HITL; compensating action recorded where reversible
      adr_reference: ADR-0011
  approved: true
  approval_notes: Approved under mandatory HITL only.

- action_type: mass_notification_send
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: Recipients come from a governed dataset, not from enumeration
    - question: D-02
      answer: no
      mitigation: Content is text; no execution path
    - question: D-03
      answer: no
      mitigation: Sending credentials held by the notification service
    - question: D-04
      answer: yes
      mitigation: >-
        Recipient lists are personal data. Mandatory HITL; the approver sees the recipient count and
        the selection criterion, not the list itself; PII filter applies to content.
      adr_reference: ADR-0012
    - question: D-05
      answer: no
      mitigation: Registered channel only
    - question: D-06
      answer: yes
      mitigation: >-
        High blast radius and hard to retract — a sent message cannot be unsent. Mandatory HITL;
        rate limit; the approver is shown that retraction is not possible.
      adr_reference: ADR-0011
  approved: true
  approval_notes: >-
    The dual-use concern here is not the individual message but the amplification: the same
    capability that notifies users can be misused to spam or to phish at scale.

- action_type: credential_or_secret_rotation
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: Operates on registered secret references only
    - question: D-02
      answer: no
      mitigation: n/a
    - question: D-03
      answer: yes
      mitigation: >-
        By definition. The agent triggers rotation through the secrets manager and never reads the
        value; the new secret is never returned into agent context or logs.
      adr_reference: ADR-0008
    - question: D-04
      answer: no
      mitigation: Secrets are not personal data
    - question: D-05
      answer: no
      mitigation: Secrets manager endpoint only
    - question: D-06
      answer: yes
      mitigation: >-
        A rotation at the wrong moment is a denial of service on every consumer of that secret.
        Mandatory HITL; rollback path recorded before execution.
      adr_reference: ADR-0011
  approved: true
  approval_notes: >-
    Approved on the condition that the agent triggers rotation and never handles the value. An
    implementation that returned the new secret to the agent would invalidate this entry.

- action_type: production_database_write
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: Writes to a declared target, no schema discovery primitive
    - question: D-02
      answer: yes
      mitigation: >-
        A write can carry a statement. Parameterised queries only; no dynamic SQL from model
        output; the sandbox executor never has production credentials.
      adr_reference: ADR-0016
    - question: D-03
      answer: no
      mitigation: Connection held by the service; the agent proposes the change, not the connection
    - question: D-04
      answer: yes
      mitigation: >-
        Production data includes L1 and L2. Mandatory HITL; bulk threshold triggers mandatory HITL
        independently; audit records the row count and the filter.
      adr_reference: ADR-0012
    - question: D-05
      answer: no
      mitigation: n/a
    - question: D-06
      answer: yes
      mitigation: >-
        Irreversible data-integrity impact. Mandatory HITL; the approver sees the exact statement and
        the affected row estimate; backup and restore path per ADR-0082.
      adr_reference: ADR-0011
  approved: true
  approval_notes: >-
    Two independent mandatory-HITL triggers apply (production environment and, above threshold,
    bulk operation). Neither may be downgraded by a risk score.

- action_type: action_on_behalf_of_high_risk_entity
  assessed_by: AI Governance Lead
  assessment_date: 2026-09-13
  dual_use_risks:
    - question: D-01
      answer: no
      mitigation: Inherits the constraints of the underlying action type
    - question: D-02
      answer: no
      mitigation: Inherits
    - question: D-03
      answer: no
      mitigation: Inherits
    - question: D-04
      answer: yes
      mitigation: >-
        The entity's classification is what makes this category exist. Mandatory HITL regardless of
        the underlying action; L1 handling rules apply throughout.
      adr_reference: ADR-0012
    - question: D-05
      answer: no
      mitigation: Inherits
    - question: D-06
      answer: yes
      mitigation: >-
        Regulatory exposure is the defining risk. Mandatory HITL; the approver is told which
        regulatory basis makes the entity high-risk.
      adr_reference: ADR-0093
  approved: true
  approval_notes: >-
    A modifier rather than a standalone capability: it raises any other action type to mandatory
    HITL. It is registered separately so that the escalation is explicit rather than implied.
```

## What this registry shows

- **All seven are approved under mandatory HITL, and none is eligible for HOTL.** Autonomy levels
  cannot reach these categories; a change would need a new ADR and full governance sign-off.
- **Five of seven answer `yes` to D-06** (harm to third parties if misused). That is expected for
  actions with real-world effect and is the reason the HITL gateway exists.
- **The recurring mitigation is a control outside the model** — a gateway, an allow-list, a
  threshold, a credential the agent never holds. No entry relies on the model choosing correctly.
- **Two entries are conditional**: secret rotation is approved only while the agent never handles
  the value, and production writes only while the sandbox executor has no production credentials.
  An implementation change that breaks either condition invalidates the entry.
