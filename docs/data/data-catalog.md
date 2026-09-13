<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data catalog

> **Owner:** Tech Lead · **Accountable per dataset:** its data owner
> **Governance:** [`data-governance-charter.md`](data-governance-charter.md) ·
> **Quality:** [`../../specs/data/data-quality.md`](../../specs/data/data-quality.md) ·
> **Contracts:** [`../../specs/data/data-contracts.md`](../../specs/data/data-contracts.md)
> **Last reviewed:** 2026-09-13

## What this is, and what it is not

This is the **governance index**: one row per dataset, naming who is accountable, what it is for,
how it is classified, whether it has a contract, what quality is expected of it, and whether it may
feed a model. It is the answer to "who do I ask about this data".

It is **not** the physical inventory. Tables, columns, migrations, encryption and index
conventions live in [`data-model-catalog.md`](data-model-catalog.md), which is a living reference
where the code wins. This catalog is a governance record where **the row wins**: a dataset whose
row says it has no contract does not get read across a domain boundary, whatever the code allows.

## Columns

| Column         | Meaning                                                                          |
| -------------- | ---------------------------------------------------------------------------------- |
| **Dataset**    | The canonical name, matching the business glossary term where one exists           |
| **Owner**      | Data owner — accountable for meaning and fitness                                    |
| **Steward**    | Keeps the entry, the rules and the glossary terms true day to day                  |
| **Custodian**  | Runs the store: access, encryption, backup, retention execution                    |
| **Class.**     | Highest PII class present (L1–L4), authoritative source `specs/privacy/pii-inventory.md` |
| **Contract**   | Contract id, or `internal` when the dataset never crosses a domain boundary        |
| **Quality**    | Rule ids, or `none declared`                                                       |
| **Model use**  | Whether it may feed or evaluate a model, and the datasheet that permits it         |

## Datasets

The corpus is a template. These rows describe the datasets its own examples use; an adopting
organisation replaces them and keeps the columns. Roles are named by role, not by person.

| Dataset                | Owner            | Steward        | Custodian | Class. | Contract      | Quality        | Model use                        |
| ---------------------- | ---------------- | -------------- | --------- | ------ | ------------- | -------------- | ---------------------------------- |
| `requests`             | platform domain  | platform eng.  | SRE       | L2     | `internal`    | none declared  | no                                 |
| `audit_events`         | platform domain  | platform eng.  | SRE       | L3     | `internal`    | none declared  | no — immutable evidence            |
| `hitl_requests_archive`| AI platform      | AI platform eng. | SRE     | L2     | `internal`    | none declared  | no                                 |
| `agent_memory_documents` | AI platform    | AI platform eng. | SRE     | L2     | `internal`    | none declared  | **yes** — datasheet required (#33) |
| `agent_context_graphs` | AI platform      | AI platform eng. | SRE     | L3     | `internal`    | none declared  | no                                 |
| `domain.request.created` | platform domain | platform eng. | SRE       | L2     | **required**  | none declared  | no                                 |
| `agent.action.approved` | AI platform     | AI platform eng. | SRE     | L2     | **required**  | none declared  | no                                 |
| Telemetry and traces   | SRE              | SRE            | SRE       | L4     | `internal`    | none declared  | no — PII redacted (ADR-0043)       |

## What this table says about the current state

Three things, stated plainly rather than left to be inferred:

1. **No dataset has declared quality rules yet.** Every row reads `none declared`. That is the
   honest state after `specs/data/data-quality.md` defined the shape and before any owner filled
   one in; it is open item 1 of that spec.
2. **Two event topics need contracts and do not have them.** They cross a domain boundary, so
   §7 of the contracts spec requires one. Until then they are a known exception, not an oversight.
3. **One dataset feeds a model.** `agent_memory_documents` is the retrieval and memory corpus, and
   under EU AI Act `ART-10` it may not do so without a datasheet. That datasheet is #33.

## Adding a dataset

1. Name it, matching [`business-glossary.md`](business-glossary.md) if a term exists.
2. Name owner, steward and custodian **by role**. An unnamed owner is a finding.
3. Classify it against `specs/privacy/pii-inventory.md`.
4. Decide `internal` or contract, per the contracts spec §7.
5. Declare at least one quality rule, or write `none declared` — deliberately, not by omission.
6. If it will ever feed or evaluate a model, write the datasheet first.

## Review

Completeness is read at the data governance council's quarterly cycle: every dataset present,
every owner named, every `none declared` still deliberate, every exception still within its expiry.

## Related

- [`data-model-catalog.md`](data-model-catalog.md) — the physical inventory
- [`business-glossary.md`](business-glossary.md) — what the names mean
- [`data-governance-charter.md`](data-governance-charter.md) — who decides
- [`../privacy/pii-inventory.md`](../privacy/pii-inventory.md) — the authoritative classification
