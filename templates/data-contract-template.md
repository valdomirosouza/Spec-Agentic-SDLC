<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Data contract: [DATASET NAME]

<!--
  Produced per specs/data/data-contracts.md. One file per contract, beside the producing domain's
  specs, registered in docs/data/data-catalog.md. The schema is REFERENCED, never copied — the
  registry stays the single source. Delete no required section; write "none, and why" instead.
-->

**Contract id:** DC-[DOMAIN]-[NNN] · **Version:** [MAJOR.MINOR] · **Status:** draft | active | deprecated | retired
**Dataset:** `[name as registered in the catalog]` · **Last updated:** [YYYY-MM-DD]

## Parties

| Role         | Who                              | Contact role         |
| ------------ | -------------------------------- | -------------------- |
| Producer     | [domain]                         | [data owner]         |
| Data steward | [role]                           | [role]               |
| Consumer     | [service / domain / agent]       | [role]               |

_An agent that reads this dataset is a consumer and is listed here._

## Schema

**Reference:** `[registry subject / OpenAPI component / Avro schema path]` · **Registry version:** [n]

Never copied here. A change to the schema is a change to this contract.

## Semantics

| Field | Meaning | Unit | Boundary convention | Null means |
| ----- | ------- | ---- | ------------------- | ---------- |
|       |         |      |                     |            |

_Be explicit where two implementations could disagree: inclusive or exclusive bounds, timezone and
epoch unit, encoding, rounding, and whether null means "absent", "unknown" or "not applicable"._

## Classification

| Field | Class (L1–L4) | Masking point | Notes |
| ----- | ------------- | ------------- | ----- |
|       |               |               |       |

_"No personal data in this dataset" is a valid and expected entry._

## Quality expectations

| Expectation | Dimension | Rule id | Threshold | Severity |
| ----------- | --------- | ------- | --------- | -------- |
|             |           | DQ-…    |           |          |

## Service level

| Element      | Value                                  |
| ------------ | -------------------------------------- |
| Freshness    | [e.g. newest record ≤ 15 min old]     |
| Latency      | [source event → available]             |
| Availability | [SLO over a rolling window]            |
| Error budget | [derived from the SLO]                 |

_Or: "None declared, because [reason]."_

## Lifecycle

| Element                  | Value                                              |
| ------------------------ | -------------------------------------------------- |
| Versioning               | MAJOR.MINOR per `specs/data/data-contracts.md` §3  |
| Minimum support window   | [≥ one quarterly council cycle]                    |
| Deprecation notice       | [how consumers are told, and how far ahead]        |
| Retirement condition     | [what must be true before the old version is gone] |

## Lineage

**Upstream:** [sources] → **transformation:** [what happens] → **this dataset** → **downstream:** [known consumers]

## History

| Version | Date | Change | Breaking | Coexistence ended |
| ------- | ---- | ------ | -------- | ----------------- |
|         |      |        | yes/no   |                   |

_A change made under the active-harm exception (§4 of the spec) is recorded here with its approver._
