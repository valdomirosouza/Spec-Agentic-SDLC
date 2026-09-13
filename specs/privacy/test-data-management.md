---
id: SPEC-PRIV-011
kind: spec
status: approved
owner: DPO
issue: 35
governing_adrs:
  - ADR-0012
  - ADR-0013
  - ADR-0018
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/privacy/pii-inventory.md
  - specs/data/data-quality.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Test data management and non-production masking

> **Owner:** DPO · **Co-owner:** Tech Lead · **Executes:** data custodian
> **Satisfies:** Constitution Art. III · ISO/IEC 42001 A.7 · GDPR Art. 5(1)(c) and LGPD Art. 6

## 1. The gap this closes

The constitution forbids real personal data in any file, and the harness enforces it on the
repository with a blocking PII scan. Neither covers the larger surface: the **non-production
environments**. A staging database restored from a production backup contains every personal
record production has, under weaker access control, longer retention and no DPIA covering that
purpose. "Test data management" and "masking in non-production" had zero occurrences in the corpus.

This is the most common way an organisation with good production controls leaks personal data.

## 2. Rules

1. **No production copy into a lower environment.** Not a restore, not a dump, not a subset, not
   "just this one table for debugging". This is the rule the rest of the spec exists to make
   practical rather than aspirational.
2. **Environments are classified.** Every environment declares the highest data class it may hold.
   Development and CI: **L4 only** (non-personal). Staging: **L3**, by exception and time-boxed.
   Production: as the dataset's own classification.
3. **Synthetic first.** Test data is generated, not derived, wherever the test does not require real
   distributions.
4. **Where realism is required, mask at the source.** Masking happens in the export path, so the
   unmasked copy never lands in the target environment. Masking after loading is not masking.
5. **Test data has retention too.** Non-production datasets expire; an environment that has not
   been refreshed or purged in a quarter is a finding.
6. **An incident in a lower environment is a real incident.** Personal data exposed in staging is
   exposed, regardless of the label on the environment.

## 3. Synthetic data for tests

| Need                           | Approach                                                                    |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Structural validity            | Generate from the schema in the data contract                                |
| Realistic distributions        | Generate from **statistics** of production, never from its records            |
| Referential integrity          | Generate the graph, not the rows, so keys resolve across datasets            |
| Edge cases                     | Hand-written fixtures for boundaries — these are the valuable ones           |
| Volume for performance tests   | Amplify synthetic records; never replay production traffic containing personal data |

Fixtures follow the synthetic-data standard already in `specs/privacy/pii-inventory.md`, so a
reviewer can tell a synthetic value from a real one **at a glance**. Values that merely look fake
are not enough: a name that happens to be real is real personal data.

## 4. Masking, when it is unavoidable

Used only where a test genuinely needs production-shaped data and synthesis cannot produce it, with
a time-boxed exception approved by the DPO.

| Technique                | Use when                                                     | Preserves                    | Warning                                                              |
| ------------------------ | -------------------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------- |
| **Redaction**            | The value is irrelevant to the test                            | Nothing                       | Breaks joins and formats                                              |
| **Deterministic masking** | Joins across datasets must still work                          | Referential integrity         | Same input always yields same output, so it is **reversible by frequency analysis** on small domains |
| **Generalisation**       | Only the band matters (age range, region)                      | Statistical shape            | Small buckets re-identify                                             |
| **Substitution**         | Realistic-looking values are needed                            | Format and type              | A substituted value can collide with a real person's                   |
| **Perturbation**         | Aggregate behaviour matters, individual values do not          | Distribution                 | Outliers survive perturbation and outliers identify people            |

**Deterministic masking is the one teams over-trust.** It is chosen precisely because it preserves
joins, and preserving joins is what makes re-identification possible. Where it is used, the mapping
key is managed as a secret and rotated, and the masked dataset keeps the classification of its
source unless a re-identification assessment says otherwise.

**Never masked, never copied:** authentication credentials, tokens, keys, and any special-category
field. These are regenerated, not transformed.

## 5. Provisioning path

1. Determine the environment's permitted class (§2.2).
2. Attempt synthesis (§3). Record that it was attempted.
3. If synthesis cannot meet the need, request a **time-boxed exception**: what test, why synthesis
   fails, which fields, which technique, expiry date. DPO approves.
4. Export **with masking applied in the export path**.
5. Load, then verify: scan the target for the source's known identifiers.
6. Record the provisioning in the environment's register with its expiry.
7. On expiry: purge, and verify the purge.

Step 5 is the step that is usually skipped and is the only one that proves the previous four worked.

## 6. Agent-specific concerns

Two cases the ordinary test-data discussion misses, and which matter here because the system is
agentic:

- **Prompts and traces are test data.** A captured prompt or an agent trace from production
  contains whatever the user typed. Replaying it in a lower environment moves personal data there.
  Traces are redacted at the collector (ADR-0043) before any replay.
- **Agent memory in non-production must not be seeded from production.** The retrieval corpus is
  L2; a staging agent indexed with production documents is a production-grade disclosure risk with
  staging-grade access control.

## 7. What is enforced today

| Obligation                                  | Enforcement                                                        |
| ------------------------------------------- | -------------------------------------------------------------------- |
| No real PII in repository fixtures          | `pii-scan` in `harness/code-check.yml` — blocking                   |
| No unmasked PII in staging logs             | `pii-validation` in `harness/staging-check.yml` — blocking          |
| Telemetry redaction before export           | ADR-0043 collector redaction — running control                      |
| No production copy into lower environments  | **Review only** — proposed gate in §8                               |
| Environment classification declared         | **Review only**                                                     |
| Provisioning exceptions time-boxed          | **Review only** — DPO register                                       |

## 8. Proposed gate for the adopting repository

A pre-deploy check for non-production environments, to sit beside the existing PII gates:

```text
name: non-prod-data-provenance
blocking: true
checks:
  - every non-production datastore declares its permitted data class
  - no restore job in the environment's configuration references a production backup
  - every active masking exception has an unexpired approval
failure: "A lower environment may hold a production copy. Provisioning must follow
          specs/privacy/test-data-management.md §5."
```

Written here as a specification of the gate, not as a gate: this corpus has no environments to
check. The adopting repository implements it.

## 9. Open items

| # | Item                                                                  | Owner            | Resolve by            |
| - | ----------------------------------------------------------------------- | ---------------- | --------------------- |
| 1 | Environment register with permitted class per environment              | Data custodian   | 2026-12-13            |
| 2 | Synthetic generator for the datasets in the catalog                    | Data stewards    | on-event: Before the next perf test |
| 3 | Re-identification assessment procedure for deterministically masked sets | DPO             | on-event: Before first exception |

## Related

- [`pii-inventory.md`](pii-inventory.md) — classification and the synthetic-data standard
- [`data-retention.md`](data-retention.md) — retention that applies to lower environments too
- [`../data/data-quality.md`](../data/data-quality.md) — masked violation samples follow the same rule
- [`../../docs/data/data-governance-charter.md`](../../docs/data/data-governance-charter.md) — who approves an exception
