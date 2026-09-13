---
id: SPEC-DATA-001
kind: spec
status: approved
owner: Tech Lead
issue: 29
governing_adrs:
  - ADR-0003
  - ADR-0012
  - ADR-0013
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/data/data-contracts.md
  - specs/privacy/pii-inventory.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data quality

> **Owner:** Tech Lead · **Accountable per dataset:** the data owner
> (`docs/data/data-governance-charter.md` §4) · **Triage:** the data steward
> **Satisfies:** ISO/IEC 42001 A.7, EU AI Act `ART-10`, NIST AI RMF MEASURE 2

## 1. Problem

The corpus has mature service-level objectives for the application — latency, errors, traffic,
saturation — and had none for the data the application produces and consumes. Quality of data, its
dimensions, its rules and its observability had zero occurrences before this spec.

For an agentic system this is the more dangerous half. A service that is fast and available while
serving stale or incomplete data lets an agent reason confidently over wrong inputs, and every
downstream control — evaluator, guardrails, human review — sees a plausible answer with no signal
that its premise was broken.

## 2. The six dimensions

Each dimension has one operational definition, so that two people measuring the same dataset get
the same number.

| Dimension        | Question it answers                                                    | Operational definition                                                                             |
| ---------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| **Completeness** | Is everything that should be here, here?                                | Share of required fields that are non-null, and share of expected records that arrived in a window  |
| **Validity**     | Does each value conform to its declared form?                           | Share of values that satisfy the field's type, range, pattern and enumeration in the contract        |
| **Accuracy**     | Does the value correspond to the real-world fact?                       | Share agreeing with an agreed reference source or a verified sample; where no reference exists, say so and do not claim accuracy |
| **Consistency**  | Do related values agree with each other, here and across datasets?      | Share of records satisfying declared cross-field and cross-dataset invariants                        |
| **Uniqueness**   | Is each real-world thing represented once?                              | 1 − (duplicate keys ÷ total keys) under the dataset's declared identity rule                        |
| **Timeliness**   | Is it here soon enough to be useful, and is it fresh?                   | Two measures: **freshness** (age of the newest record) and **latency** (source event to availability) |

**Accuracy is the honest one.** It is the dimension most often claimed and least often measured,
because it needs a reference the organisation usually does not have. A dataset with no reference
source declares accuracy as `not measured` rather than assuming a number (Constitution IX).

## 3. Rules

A rule is the smallest testable statement of an expectation.

```yaml
# One entry per rule, in the dataset's contract or alongside its pipeline.
- id: DQ-REQ-001
  dataset: requests            # as named in docs/data/data-catalog.md
  dimension: completeness
  rule: "request_id, created_at and status are non-null"
  measure: "count(rows where any of the three is null) / count(rows)"
  threshold: "== 0"            # violation at the first failing row
  severity: critical
  on_violation: block          # block | alert | record
  owner: data owner of `requests`
```

| Field          | Meaning                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------- |
| `dimension`    | One of the six. A rule that fits none is not a quality rule                                  |
| `measure`      | How the number is computed, precisely enough to reimplement                                  |
| `threshold`    | The boundary and its direction; boundary conventions follow the dataset's contract            |
| `severity`     | `critical` · `major` · `minor`                                                                |
| `on_violation` | `block` stops the pipeline · `alert` pages the steward · `record` writes a finding only       |

**Every declared expectation has at least one rule.** An expectation stated in prose and not
expressed as a rule is an assumption, and is treated as one at review.

## 4. Severity and response

| Severity     | Meaning                                                                    | Response                                                                         |
| ------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **critical** | The data would cause a wrong decision, or is unusable                       | `block`: stop the pipeline, do not publish, page the steward                       |
| **major**    | A material share is wrong but the dataset remains usable                     | `alert`: publish with the violation recorded and visible to consumers              |
| **minor**    | Cosmetic or bounded deviation                                                | `record`: finding in the quality report, reviewed at the council's quarterly cycle |

**A dataset that feeds a model or an agent decision has no `minor` completeness or validity
rules.** Either the field matters, in which case its absence is at least `major`, or it does not,
in which case it should not be in the contract.

## 5. Service-level objectives for data

Data SLOs follow the same shape as the service SLOs in `docs/sre/slo/`, so that one review reads
both.

| Element        | Example for a consumer-visible dataset                                            |
| -------------- | ----------------------------------------------------------------------------------- |
| **SLI**        | Share of hourly windows where freshness ≤ 15 min and completeness = 100%           |
| **SLO**        | 99% of windows over 30 rolling days                                                 |
| **Error budget** | 1% of windows — roughly 7 hours per 30 days                                       |
| **Burn alert** | Two consecutive windows failing, or 25% of the budget consumed in 24 h             |
| **Consequence** | Budget exhausted: no new consumers onboarded and no non-critical schema change until it recovers |

Each dataset in the catalog declares its SLIs and SLOs, or declares explicitly that it has none
and why. "No SLO" is an acceptable answer for an internal, single-consumer dataset; silence is not.

## 6. Observability

| What                    | Where it goes                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------- |
| Rule results per run    | A metric per rule id with dataset, dimension and outcome labels                       |
| Freshness and latency   | A gauge per dataset, published even when no rule failed                               |
| Violation events        | A structured log with rule id, dataset, count, sample **of masked values only**       |
| Quality report          | Rolled up per dataset, read at the council's quarterly cycle                          |

**Two rules on violation samples.** Never include raw values from an L1 or L2 field in a violation
log — mask first, exactly as the pipeline would (Constitution Art. III). And never suppress a
violation because the sample cannot be shown: record the count and the rule, without the sample.

## 7. Where quality is checked

| Point                          | What runs there                                                              |
| ------------------------------ | ------------------------------------------------------------------------------ |
| **Ingestion**                  | Validity and completeness on the inbound contract; reject or quarantine early  |
| **After transformation**       | Consistency and uniqueness; the transformation is the usual culprit            |
| **Before publication**         | The full rule set for the dataset's declared expectations; `block` rules bind here |
| **Continuously in production** | Freshness and latency, which cannot be checked once and assumed               |
| **Before a model uses it**     | The dataset's rules plus the datasheet check (EU AI Act `ART-10`)             |

Checking only at ingestion is the most common mistake: most quality loss happens in
transformation, downstream of the only place many teams measure.

## 8. Incidents

A quality violation at `critical`, or a `major` violation persisting beyond one cycle, is a **data
incident**. It follows the ordinary incident path with three additions:

1. **Blast radius first.** Which consumers read the bad data, and did any decision or model
   consume it? Lineage (`specs/data/data-lineage.md`, #32) answers this; until it exists, the
   consumer list in the contract is the fallback.
2. **Correct, then backfill, then notify** — in that order. Notifying before correcting invites
   consumers to build workarounds that outlive the incident.
3. **Every incident yields a rule.** If the violation was not caught by an existing rule, the
   postmortem adds one. The rule count for a dataset does not decrease, mirroring the abuse-case
   ratchet of ADR-0050.

## 9. What is enforced today

| Obligation                                   | Enforcement                                                         |
| -------------------------------------------- | --------------------------------------------------------------------- |
| No real personal data in fixtures            | `pii-scan` in `harness/code-check.yml` — blocking                    |
| Schema validity at the contract boundary     | Contract-drift gate                                                  |
| Rules declared per dataset                   | **Review only** — the catalog entry is checked by a human           |
| Rules executed in the pipeline               | **Adopter** — the product repository runs them                       |
| SLOs declared per consumer-visible dataset   | **Review only**                                                      |

The corpus defines the rules; the adopting repository runs them. Nothing here claims to execute a
check this repository cannot execute.

## 10. Open items

| # | Item                                                                | Owner       | Resolve by          |
| - | --------------------------------------------------------------------- | ----------- | ------------------- |
| 1 | First rule set for the datasets in the catalog                       | Data owners | Next quarterly cycle |
| 2 | Reference source for any dataset claiming an accuracy target         | Data owners | Before claiming it   |
| 3 | Lineage available for blast-radius analysis (#32)                    | Tech Lead   | With #32             |

## Related

- `docs/data/data-governance-charter.md` — roles, council, exceptions
- [`data-contracts.md`](data-contracts.md) — where a dataset's expectations are promised
- `docs/data/data-catalog.md` (#31) — where rules and SLOs are registered per dataset
- [`../privacy/pii-inventory.md`](../privacy/pii-inventory.md) — classification that constrains violation samples
