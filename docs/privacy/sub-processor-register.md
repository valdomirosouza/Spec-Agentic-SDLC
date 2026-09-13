<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Sub-processor register

> **Owner:** DPO · **Reviewed:** quarterly, and on every addition
> **Companion:** [`data-processing-register.md`](data-processing-register.md) (the activities) ·
> [ADR-0094](../adr/ADR-0094-data-residency-and-sovereignty.md) (residency per class)
> **Last reviewed:** 2026-09-13

## What this is

The processing register answers *what personal data we process and why*. It names processors
inside the activity rows — "LLM provider", "log aggregation provider" — but it never lists them as
entities with a region, a contract and a review date. "Sub-processor" had zero occurrences in the
corpus, and the contracts appeared as placeholder identifiers such as `DPA-<ID>`.

That gap matters for three concrete reasons: a customer's DPA usually obliges us to publish the
list and to notify before adding to it, a data-subject erasure request has to reach every
sub-processor holding a copy, and a residency assessment (ADR-0094) is impossible without knowing
where each one processes.

**Terminology.** The organisation is the **controller** for its own processing and a **processor**
for a customer's data. The parties below are **sub-processors** in the second case and processors
in the first; the register is kept once, from the customer's point of view, because that is the
view a customer asks for.

## Register

Roles rather than vendor names, because the corpus is a template. An adopting organisation replaces
each row with its actual provider and keeps every column. **A row with an unknown region or an
unverified contract is a finding, not a placeholder.**

| # | Sub-processor            | Service provided                       | Personal data it can access                      | Class | Processing region        | Transfer instrument        | Contract | Assessed   | Notes |
| - | ------------------------ | -------------------------------------- | -------------------------------------------------- | ----- | ------------------------ | -------------------------- | -------- | ---------- | ----- |
| 1 | Cloud infrastructure provider | Compute, storage, managed database | All data at rest in the primary region             | L1–L3 | *adopter's primary region* | n/a if in-region         | DPA required | **pending** | The broadest access of any entry |
| 2 | Foundation model provider | LLM inference                         | Whatever reaches a prompt, tool argument or retrieval result | L2 (L1 prohibited, ADR-0094 §2) | US (`docs/dependency-manifest.yaml`) | required for EU data | DPA in place: no training on submitted data | **pending** | Region is a governed fact re-verified at model promotion |
| 3 | Log aggregation provider | Log storage and search                 | Whatever appears in logs after masking             | L3    | *adopter-specific*        | per destination           | DPA in place | **pending** | Masking is the control that keeps this L3 |
| 4 | Telemetry backend        | Traces and metrics                     | L4 after collector redaction (ADR-0043); class of source before it | L4 | *adopter-specific* | per destination | DPA required | **pending** | Redaction must run **before** export, not after |
| 5 | Analytics platform       | Product analytics                      | Usage events                                       | L3    | *adopter-specific*        | per destination           | DPA in place | **pending** | |
| 6 | Vector store provider *(if managed)* | Embedding storage and search | The retrieval corpus, L2, encrypted at rest       | L2    | *adopter-specific*        | per destination           | DPA required | **pending** | Embeddings of personal text remain personal data |

**Every row is `pending` assessment.** That is the true state of a template that has never run a
supplier assessment, and recording it is more useful than an invented date (Constitution IX).

## Adding a sub-processor

1. **Assess before contracting.** Security posture, region, sub-processors of its own, incident
   history, and whether it trains on or retains customer data.
2. **Contract.** A data processing agreement with the mandatory terms, including the flow-down
   obligation that it may not appoint its own sub-processor without notice.
3. **Transfer instrument** where the region requires one, recorded per destination.
4. **Residency check** against ADR-0094 for every class it can access. An entry that can reach L1
   outside the primary region is refused, not mitigated.
5. **Notify customers** where a DPA requires it, with the notice period that DPA sets, **before**
   the sub-processor begins processing.
6. **Register the row** here, and add the processor to the matching activity in the processing
   register.
7. **Update the DPIA** for any activity whose risk profile changes.

Steps 5 and 7 are the ones that get skipped under delivery pressure, and both are the ones a
customer audit checks first.

## Removing one

Removal is not deletion of the row. Mark it **retired** with the date, confirm the sub-processor
has deleted or returned the data as the contract requires, obtain that confirmation in writing, and
keep the row for the retention period of the underlying activity. A retired row with no deletion
confirmation is an open item, not a closed one.

## Review

| When            | What is checked                                                                             |
| --------------- | --------------------------------------------------------------------------------------------- |
| Quarterly       | Every row's region, contract status and assessment date still current; expired assessments raised |
| On addition     | The seven steps above, evidenced                                                             |
| On model change | Row 2's processing region re-verified (ADR-0094 §2)                                          |
| On incident     | Whether a sub-processor was involved, and whether notification obligations were triggered    |

## Open items

| # | Item                                                              | Owner | Resolve by            |
| - | ------------------------------------------------------------------- | ----- | --------------------- |
| 1 | Supplier assessment performed for every row (all are `pending`)    | DPO   | Next quarterly review |
| 2 | Real provider names, regions and contract references               | Adopting organisation | Before first customer DPA |
| 3 | Customer notification procedure and notice period                  | DPO   | Before adding a sub-processor |

## Related

- [`data-processing-register.md`](data-processing-register.md) — the activities these serve
- [ADR-0094](../adr/ADR-0094-data-residency-and-sovereignty.md) — residency per class
- [`../compliance/dependency-policy.md`](../compliance/dependency-policy.md) — the supply-chain counterpart
- [`../../specs/privacy/training-data-governance.md`](../../specs/privacy/training-data-governance.md) — licensed datasets and their suppliers
