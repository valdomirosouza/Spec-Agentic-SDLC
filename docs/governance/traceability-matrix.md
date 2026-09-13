<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Traceability Matrix

> **Owner:** Tech Lead · **Status:** Living document · **Last updated:** 2026-06-14
> Maps every service in [`services.yaml`](../../services.yaml) to its governing spec, ADRs, SLO,
> runbooks, dashboard, and tests, so engineers, auditors, and AI agents can confirm coverage in
> one place. This addresses Wave 1 (Traceability Hardening) of the repository improvement plan.

## How this is enforced

The **machine-checkable** columns are validated in CI by `make verify-traceability` (deterministic,
blocking). The remaining columns are maintained by hand and reviewed in PR.

| Column                   | Enforced by                                     | Mode     |
| ------------------------ | ----------------------------------------------- | -------- |
| ADRs exist               | `scripts/governance/check_traceability.py`      | Blocking |
| Topic → schema exists    | `scripts/governance/check_traceability.py`      | Blocking |
| publish/subscribe valid  | `scripts/governance/check_traceability.py`      | Blocking |
| `depends_on` valid       | `scripts/governance/check_traceability.py`      | Blocking |
| Per-service SLO file     | `scripts/governance/check_service_slo_files.py` | Blocking |
| Runbook links resolve    | `scripts/governance/check_runbook_links.py`     | Blocking |
| Spec / dashboard / tests | manual review (no canonical machine link yet)   | Review   |

Run locally: `make verify-traceability`.

## Service → artifact matrix

Legend: ✓ dedicated artifact · ▣ covered by a system-level artifact · — not applicable.
"Canary SLO" is the per-service `docs/sre/slo/<name>.yaml` read by `cd-production.yml` (ADR-0073);
only `type: api` services require one (workers/jobs/static frontend roll out by other paths).

| Service          | Type     | Owner         | Spec                                                                                     | Governing ADRs (services.yaml)     | Canary SLO (`docs/sre/slo/`)                              | 30-day SLO                    | Runbooks                                                                                  | Dashboard                                  | Tests                                   |
| ---------------- | -------- | ------------- | ---------------------------------------------------------------------------------------- | ---------------------------------- | --------------------------------------------------------- | ----------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------- |
| `api-gateway`    | api      | platform-team | ▣ `specs/system/request-pipeline.md`, `specs/system/architecture.md`                     | 0002, 0010, 0011, 0014, 0015       | ✓ `api-gateway.yaml`                                      | ▣ `slo.yaml`                  | `docs/runbooks/rollback-procedure.md`, `docs/sre/runbooks/api-gateway-high-error-rate.md` | `golden-signals.json`, `sre-overview.json` | `tests/unit/`, `tests/integration/`     |
| `domain-service` | api      | domain-team   | ▣ `specs/system/architecture.md`, `specs/api/async-api-design.md`                        | 0002, 0003, 0011                   | ✓ `domain-service.yaml` _(template defaults — [CONFIRM])_ | ▣ `slo.yaml`                  | `docs/runbooks/RB-004-db-connection-failure.md`                                           | `sre-overview.json`                        | `services/domain-service/src/test/`     |
| `golden-signals` | api      | sre-team      | ✓ `specs/system/SPEC-LGS-001-log-based-golden-signals.md` (+ feature spec, threat model) | 0066, 0067, 0068, 0069, 0012, 0026 | ✓ `golden-signals.yaml`                                   | ✓ `golden-signals-slo.yaml`   | `docs/sre/runbooks/RB-SRE-GS-001-store-unavailable.md`, `RB-SRE-GS-002-freshness-lag.md`  | `golden-signals.json`                      | `services/golden-signals/src/test/`     |
| `event-worker`   | worker   | platform-team | ▣ `specs/system/async-event-flow.md`                                                     | 0002, 0003, 0005                   | — (not canary-deployed)                                   | ▣ `slo.yaml` (event-consumer) | `docs/sre/runbooks/kafka-consumer-lag.md`, `docs/sre/runbooks/dlq-accumulating.md`        | `sre-overview.json`                        | `tests/unit/`, `services/event-worker/` |
| `frontend`       | frontend | frontend-team | ▣ `specs/ai/hitl-hotl.md` (operator UI)                                                  | 0002, 0011                         | — (static deploy)                                         | —                             | `docs/runbooks/README.md`                                                                 | —                                          | `frontend/` (Playwright e2e planned)    |
| `batch-jobs`     | job      | platform-team | ▣ `specs/privacy/data-retention.md`                                                      | 0013, 0011                         | — (CronJob)                                               | —                             | `docs/runbooks/README.md`                                                                 | `sre-overview.json`                        | `tests/unit/`                           |

## Notes & known gaps

- **Spec column is system-level (▣) for most services.** Only `golden-signals` has a dedicated
  `SPEC-LGS-001`. Per-service feature specs are a Wave-3 follow-up; until then the system specs
  (`request-pipeline`, `architecture`, `async-event-flow`) are the authoritative references.
- **`domain-service.yaml` / `golden-signals.yaml` canary thresholds are starter values** marked
  `[CONFIRM]` — they need SRE-Lead sign-off and measured baselines before they gate a real rollout.
  They exist so `cd-production.yml` is _executable_ for every `type: api` service (previously only
  `api-gateway` had a canary SLO file, so a deploy of any other API service hard-failed at the
  `load-slo` step).
- **Spec ↔ service is not yet machine-linked.** `check_traceability.py` validates ADRs, topics,
  schemas, deps, and SLO presence; wiring a `spec:` field into `services.yaml` and validating it is
  a recommended Wave-3 enhancement.

## Related

- `services.yaml` — canonical service registry (CLAUDE.md §0.1)
- `docs/sre/slo/` — SLO definitions · schema: `docs/sre/slo/schema/service-slo.schema.json`
- `docs/runbooks/README.md` — runbook namespaces (ADR-0033)
- ADR-0073 — SLO-driven canary thresholds
