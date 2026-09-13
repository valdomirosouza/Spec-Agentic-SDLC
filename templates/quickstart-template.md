# Quickstart: [FEATURE NAME]

**Spec**: `spec.md` | **Plan**: `plan.md` | **Phase**: 5 / Phase 1 design → executed at Phase 6 and 8

<!--
  Produced by /sdd-plan (step 7). Runnable validation scenarios — one per acceptance criterion
  (spec §9). Each states prerequisites, the exact command and the expected outcome. No
  implementation bodies. /sdd-implement runs these at completion; /sdd-converge checks that
  every AC has a scenario. Worked example:
  specs/features/SPEC-LGS-001-log-based-golden-signals/quickstart.md
-->

## Prerequisites

```bash
# environment variables, services to start, fixtures to load
```

## Scenario 1 — [Title] (AC-01, FR-NN)

```bash
# command
# → expected output / status code
```

Expected: [observable outcome in one sentence].

## Scenario 2 — [Title] (AC-02, FR-NN)

```bash
```

## Coverage

| AC    | Scenario | Automated test (from spec §9) |
| ----- | -------- | ----------------------------- |
| AC-01 | 1        | `tests/…`                     |

_Every AC in spec §9 appears here; a missing row is a /sdd-analyze finding._
