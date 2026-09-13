# Data Model: [FEATURE NAME]

**Spec**: `spec.md` §4 Key Entities | **Plan**: `plan.md` | **Phase**: 5 / Phase 1 design (ADR-0058)

<!--
  Produced by /sdd-plan (step 7). Entities, fields, validation rules and state transitions
  derived from the spec — no storage engine details beyond what the plan decided. Field
  constraints are quoted verbatim by /sdd-tasks, so be exact (types, ranges, required).
  Flag every PII field with its L1–L4 class and masking point (Constitution III).
  Worked example: specs/features/SPEC-LGS-001-log-based-golden-signals/data-model.md
-->

## Entities

### [Entity] _([origin — inbound / derived / persisted] — FR-NN)_

| Field   | Type    | Validation                      | Notes |
| ------- | ------- | ------------------------------- | ----- |
| `id`    | string  | required; format …              |       |
| `…`     |         |                                 |       |

**Relationships**: [Entity] 1—n [Entity] …

**State transitions**: `created` → `…` → `…` (who or what triggers each; terminal states).

### [Next entity]

## Identifiers and keys

[Primary identifiers, uniqueness rules, key grammar if a key-value store is involved — cite the
ADR that fixes it.]

## Retention and lifecycle

| Data        | Retention | Measured from | Deletion / supersession path |
| ----------- | --------- | ------------- | ---------------------------- |
|             |           |               |                              |

## PII classification _(Constitution III)_

| Field | Class (L1–L4) | Masking point | Stored form | DPIA/RIPD |
| ----- | ------------- | ------------- | ----------- | --------- |
|       |               |               |             |           |

_"None — no personal data" is a valid row when true._
