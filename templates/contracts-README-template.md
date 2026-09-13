# Contracts: [FEATURE NAME]

<!--
  Produced by /sdd-plan (step 7) as contracts/README.md. One file per interface delta:
  REST → OpenAPI 3.1 delta · events → AsyncAPI delta + Avro schema · CLI → command reference.
  The adopting repository merges deltas into its published contracts (docs/api/…) and
  generates clients and stubs from them — stubs are never hand-written. Topics added here must
  also be registered in the adopting repository's service registry (services.yaml) when it has one.
  Worked example: specs/features/SPEC-LGS-001-log-based-golden-signals/contracts/
-->

Interface deltas produced at Phase 1 of the plan (Constitution VII: every contract traces to an FR).

| File                   | Kind          | Covers        |
| ---------------------- | ------------- | ------------- |
| `openapi-delta.yaml`   | OpenAPI 3.1   | FR-NN, FR-NN  |
| `asyncapi-delta.yaml`  | AsyncAPI 3.0  | FR-NN         |
| `<event>.avsc`         | Avro schema   | FR-NN         |

Delete the rows that do not apply; "No external interface changes" is a valid README.
