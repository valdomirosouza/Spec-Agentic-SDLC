---
id: SPEC-DATA-002
kind: spec
status: approved
owner: Tech Lead
issue: 30
governing_adrs:
  - ADR-0003
  - ADR-0024
  - ADR-0047
new_adrs_required: []
implemented_by: []
verified_by: []
related_specs:
  - specs/data/data-quality.md
  - specs/api/async-api-design.md
last_updated: 2026-09-13
---

<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data contracts

> **Owner:** Tech Lead · **Accountable per contract:** the data owner
> **Template:** [`../../templates/data-contract-template.md`](../../templates/data-contract-template.md)
> **Satisfies:** ISO/IEC 42001 A.7 · NIST AI RMF MAP 2 · EU AI Act `ART-10` (for model-facing data)

## 1. What this adds to what already exists

The corpus already governs **schemas**: a registry with backward compatibility required, an
explicit list of breaking and non-breaking changes (ADR-0024), published OpenAPI and AsyncAPI
documents, and a contract-drift gate that blocks a PR when they diverge. That is real and it works.

What it did not have is the **contract around the schema**. A schema says what the bytes look
like. It does not say who promises them, to whom, what the values mean, how fresh they are, how
good they are, how long the producer will keep serving this version, or what happens when that
ends. Those are the questions a consumer actually depends on, and before this spec they lived in
people's heads.

A data contract is therefore **not a new artefact competing with the schema**. It is the schema
plus the six things around it that were previously unwritten.

## 2. Anatomy

| Part                    | What it fixes                                                                                    | Required |
| ----------------------- | -------------------------------------------------------------------------------------------------- | -------- |
| **Identity**            | Contract id, dataset name, version, status (`draft` · `active` · `deprecated` · `retired`)         | Yes      |
| **Parties**             | Producer (domain + data owner) and known consumers, each with a contact role                       | Yes      |
| **Schema**              | A reference to the registered schema, never a copy — the registry stays the single source          | Yes      |
| **Semantics**           | What each non-obvious field *means*, its unit, its boundary convention, its null semantics         | Yes      |
| **Classification**      | L1–L4 per field, and the masking point if any (Constitution Art. III)                              | Yes      |
| **Quality**             | The declared expectations and the rule ids that measure them (`specs/data/data-quality.md`)       | Yes      |
| **Service level**       | Freshness, latency, availability and the error budget, or an explicit "none, and why"              | Yes      |
| **Lifecycle**           | Versioning scheme, deprecation policy, minimum support window, retirement conditions              | Yes      |
| **Lineage**             | Upstream sources and the transformation that produces this dataset                                | When known |

**The three fields that carry the most weight** are semantics, boundary conventions and null
semantics — because they are where two conformant implementations silently disagree. The corpus
already learned this the hard way: ADR-0068 records three different "URL encoders" producing three
different keys for the same path, and the golden-signals spec had to pin `>=` for saturation,
`>= 400` for errors and a strict `>` for the threshold flip. Contracts state these explicitly.

## 3. Versioning

`MAJOR.MINOR`:

- **MINOR** — additive and backward compatible: a new optional field, a widened enumeration a
  consumer may ignore, a relaxed constraint, better documentation. No consumer action required.
- **MAJOR** — anything a conformant consumer could break on. The list of what counts is ADR-0024's;
  this spec does not restate it, because two lists drift.

A contract's version is independent of the producing service's version. A service release that
does not change the contract does not bump it.

## 4. Breaking changes

A breaking change is a **process**, not an event.

| Step | What happens                                                                                                 | Who                  |
| ---- | -------------------------------------------------------------------------------------------------------------- | -------------------- |
| 1    | **Proposal** — new version drafted with the rationale and the consumer impact, one line per known consumer     | Data owner           |
| 2    | **Notice** — consumers informed with the migration note and the coexistence window's end date                 | Data owner           |
| 3    | **Coexistence** — both versions served; the old one is marked `deprecated`, never silently degraded           | Producer             |
| 4    | **Migration** — each consumer confirms it has moved, or asks for an extension before the window closes        | Consumers            |
| 5    | **Retirement** — old version withdrawn; contract status `retired`; registry and catalog updated               | Data owner           |

**Minimum coexistence window: one full quarterly council cycle**, or longer when any consumer's
own release cadence is slower. **An unanswered consumer is not a migrated consumer**: silence
extends the window and escalates to the council, it does not authorise retirement.

**The one case that skips the process** is a change required to stop an active harm — a field
leaking personal data, or a value that causes a wrong decision with real effect. Then the change
is immediate, the DPO or Security Lead approves it, and the notice follows rather than precedes.
That exception is recorded in the contract's history.

## 5. Relationship to the existing gates

| Existing mechanism            | What it checks                                    | What the contract adds                                        |
| ----------------------------- | ------------------------------------------------- | --------------------------------------------------------------- |
| Schema registry compatibility | The new schema is readable by the old reader      | Whether the *meaning* changed even when the bytes are compatible |
| Contract-drift gate           | Published documents match the registered schema   | Whether a consumer was told, and whether the window was honoured |
| Data quality rules            | The values are within expectation                 | Which expectations were promised, and to whom                   |

A change can pass every automated gate and still break a consumer: widening an enumeration is
backward compatible in the registry and semantically breaking for a consumer that switches on it.
The contract is where that is caught, by a human, before the notice period starts.

## 6. Where contracts live

- One Markdown file per contract from
  [`../../templates/data-contract-template.md`](../../templates/data-contract-template.md), beside
  the producing domain's specs.
- Registered in `docs/data/data-catalog.md` (#31), which is the index.
- The schema stays in the registry; the contract links to it and never copies it.

## 7. When a contract is required

| Situation                                                | Contract required                    |
| -------------------------------------------------------- | -------------------------------------- |
| Dataset read only inside the producing domain            | No — catalog entry is enough          |
| Dataset read by another domain or another service        | **Yes**                                |
| Dataset published on an event topic                      | **Yes**                                |
| Dataset exposed through a public or partner API          | **Yes**                                |
| Dataset that feeds or evaluates a model                  | **Yes**, plus a datasheet (#33)        |
| Dataset that feeds an agent's context or memory          | **Yes** — the agent is a consumer      |

The last row is the one teams forget. An agent reading a dataset is a consumer with no ability to
complain about a silent semantic change, which makes the contract more important there, not less.

## 8. What is enforced today

| Obligation                          | Enforcement                                              |
| ----------------------------------- | ---------------------------------------------------------- |
| Schema compatibility                | Contract-drift gate — blocking                            |
| Published documents match registry  | Contract-drift gate — blocking                            |
| Contract exists for a cross-domain dataset | **Review only** — catalog completeness at the council cycle |
| Coexistence window honoured         | **Review only**                                            |

## Related

- [`data-quality.md`](data-quality.md) — the expectations a contract promises
- [`../api/async-api-design.md`](../api/async-api-design.md) — event schema rules this builds on
- `docs/data/data-catalog.md` (#31) — the contract index
- `docs/data/data-governance-charter.md` — who approves a breaking change
