# Contracts: Log-Based Golden Signals

Interface deltas produced at Phase 1 of the plan (Constitution VII: every contract traces to an
FR). This feature adds five REST paths and no events.

| File                  | Kind          | Covers                     |
| --------------------- | ------------- | -------------------------- |
| `openapi-delta.yaml`  | OpenAPI 3.1   | FR-01, FR-07…FR-14         |

The adopting repository merges the delta into its published `docs/api/openapi/v1/openapi.yaml`
and generates clients from it; stubs are never hand-written.
