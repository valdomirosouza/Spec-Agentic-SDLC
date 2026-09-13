# Implementation Plan: Log-Based Golden Signals

**Spec**: `specs/features/SPEC-LGS-001-log-based-golden-signals/spec.md` | **Branch**: `feature/SPEC-LGS-001-log-based-golden-signals` | **Date**: 2026-09-12
**Phase**: 5 — Architecture & Technical Design (ADR-0058) | **Risk class**: high

<!--
  Produced by /sdd-plan. Worked example of the feature bundle (ADR-0090). The design decisions
  below are the ones already accepted in ADR-0066 (runtime), ADR-0067 (store), ADR-0068
  (extraction rules, windows, key grammar) and ADR-0069 (queue); this plan binds them to the
  spec's FRs and records what Phase 6 must build.
-->

## Summary

Deliver one Spring Boot service, `services/golden-signals`, that validates and masks HAProxy log
batches, extracts the four Golden Signals, aggregates them through a bounded in-JVM queue into
1m/5m epoch-aligned buckets in Redis (TTL retention), and serves rank-interpolated percentiles
with a governance block behind API-key auth, rate limiting and an append-only audit trail.

## Technical Context

**Language/Version**: Java 21 (virtual threads) — ADR-0066
**Primary Dependencies**: Spring Boot 3.5.x (`spring-boot-starter-web`, `-validation`, `-data-redis` with Lettuce), Micrometer + OpenTelemetry; no external statistics library (FR-07)
**Storage**: Redis single node, dedicated `gs-redis` instance, TLS in production (`rediss://`, ADR-0019) — ADR-0067
**Messaging**: none externally; in-JVM `ArrayBlockingQueue` (ADR-0069). Kafka is the recorded scale-out seam; no topic is registered in this cycle
**Testing**: JUnit 5 for `domain`; `@SpringBootTest` with the in-memory store profile; Testcontainers-Redis for the `redis` profile; abuse cases mirrored from `tests/abuse_cases/` markers
**Target Platform**: one K8s/Compose service exposing `/ingestion`, `/analytics*`, `/audit`
**Performance Goals**: `/analytics` p95 ≤ 300 ms over 24 h of 5m buckets (NFR-07); ingestion never blocks on a full queue
**Constraints**: no raw client IP past the ingestion filter; no external stats library; config via env only; single deployable (cost envelope, ADR-0020)
**Scale/Scope**: single node; queue capacity 10 000 events; ≥ 5 paths in fixtures; ~1k entries/min in the acceptance run

## Constitution Check

_GATE: must pass before Phase 0 research; re-checked after Phase 1 design. Cite the article._

| Article               | Question the plan must answer                                        | Status (pass / justified / FAIL) |
| --------------------- | -------------------------------------------------------------------- | -------------------------------- |
| I Specification First | Is the spec `approved`? Does every plan decision trace to an FR/NFR? | **justified** — spec is `draft`; this plan was drafted for the worked example and must not enter Phase 6 until the Spec-as-PR is approved. Every section cites FR/NFR ids. |
| II Test-Backed Change | Which tests fail first? Which coverage floors apply?                 | pass — AC-02…AC-10 tests listed in tasks.md precede code; ≥ 80% on `domain` (NFR-05) |
| III Privacy by Design | New PII? Class? Masking point? DPIA needed?                          | pass — `client_ip` L2, masked in `IpMasker` before queueing; RIPD entry; full-DPIA decision open with DPO (A2) |
| IV Security Gates     | New attack surface? STRIDE pass done? Controls in the matrices?      | **justified** — new ingestion boundary and agent-facing API; STRIDE pass scheduled in tasks.md (T006) before US2 closes; ASVS V2/V4/V5/V7 rows named |
| V Human Oversight     | New agent action types? Autonomy level? HITL route?                  | pass — the service emits guidance only; the copilot's HITL route is unchanged (ADR-0011) |
| VI Observability      | Golden Signals, SLO, runbook, rollback indicator defined?            | pass — see Observability Design |
| VII Traceability      | Spec id, ADR id(s), issue number present on every artefact?          | **justified** — `issue: null` until the GitHub issue is opened at Phase 1; ADR ids present |
| VIII Simplicity       | Any abstraction/project beyond what the spec needs? (see below)      | **justified** — `MetricStore` interface with two implementations (Complexity Tracking) |
| IX Grounding          | Every API/config claim verified? Unknowns marked?                    | pass — Spring/Lettuce/Loom claims verified against ADR-0066/0067/0069; rate-limiter algorithm marked `uncertain — verify` in research.md R7 |

## Phase 5 Obligations (this repository)

- **ADR required?** no new ADR — ADR-0066, ADR-0067, ADR-0068, ADR-0069 are Accepted and cover runtime, store, extraction and queue.
- **Threat model delta?** yes → `specs/security/threat-model-SPEC-LGS-001.md` (STRIDE over the ingestion boundary and the agent-facing analytics surface; task T006).
- **DPIA / RIPD?** RIPD entry yes → `docs/privacy/ripd/`; full DPIA — DPO decision at the Discovery gate (spec A2).
- **Phase 10 (AI Safety) mandatory?** yes — the output is consumed by an autonomous agent and carries the HITL/HOTL recommendation (FR-12/13).

## Project Structure

### Documentation (this feature)

```text
specs/features/SPEC-LGS-001-log-based-golden-signals/
├── spec.md              # Phase 4 output (/sdd-specify, /sdd-clarify)
├── plan.md              # This file (/sdd-plan)
├── research.md          # Phase 0 output — decisions, rationale, alternatives
├── data-model.md        # Phase 1 output — entities, fields, state transitions
├── contracts/           # Phase 1 output — OpenAPI delta
├── quickstart.md        # Phase 1 output — runnable validation scenarios
├── checklists/          # requirements.md (built-in) + reviewer checklists
└── tasks.md             # /sdd-tasks output
```

### Source Code

```text
services/golden-signals/
├── pom.xml
├── src/main/java/com/yourorg/goldensignals/
│   ├── api/         IngestionController · AnalyticsController · AuditController
│   │                ApiKeyFilter · RateLimiter · TraceIdFilter · GlobalExceptionHandler
│   ├── domain/      IpMasker · SignalExtractor · WindowBucketer · Aggregate
│   │                PercentileCalculator · GovernanceEvaluator · records (LogEntry, SignalEvent, Bucket)
│   ├── queue/       IngestQueue · AggregationWorker
│   └── infra/       MetricStore · InMemoryMetricStore · RedisMetricStore · AuditStore
└── src/test/java/…  unit (domain) · integration (@SpringBootTest) · abuse
```

**Structure Decision**: one deployable with four in-JVM modules decoupled by the bounded queue
(ADR-0069), rather than four micro-deployables. Honours NFR-01 and the ADR-0020 cost envelope;
the `IngestQueue` and `MetricStore` interfaces are the seams for Kafka and a TSDB later.

## Configuration (NFR-04)

| Env var                              | Default      | Meaning                                                  |
| ------------------------------------ | ------------ | -------------------------------------------------------- |
| `GS_API_KEYS`                        | _(required)_ | comma-separated valid API keys, compared constant-time   |
| `INGEST_QUEUE_CAPACITY`              | `10000`      | bounded queue size (ADR-0069)                            |
| `SATURATION_BYTES_THRESHOLD`         | `1048576`    | 1 MiB; `bytes_sent >=` ⇒ saturated (ADR-0068)            |
| `SATURATION_BYTES_THRESHOLD__<path>` | —            | optional per-path override, path percent-encoded         |
| `RETENTION_1M_SECONDS`               | `7200`       | 1m-window TTL (ADR-0067)                                 |
| `RETENTION_5M_SECONDS`               | `86400`      | 5m-window TTL (ADR-0067)                                 |
| `RATE_LIMIT_PER_MINUTE`              | `600`        | per-key sliding-window ingestion cap (FR-11)             |
| `HITL_P99_LATENCY_MS`                | `1000`       | strict `>` ⇒ HITL flip (FR-13)                           |
| `HITL_ERROR_RATE`                    | `0.05`       | strict `>` ⇒ HITL flip (FR-13)                           |
| `SPRING_PROFILES_ACTIVE`             | _(none)_     | `redis` selects `RedisMetricStore`; default in-memory    |

## Phase 0 — Outline & Research → `research.md`

Eight decisions (R1–R8): queue mechanism, store, extraction and key grammar, topology, percentile
method, runtime stack, rate-limiter algorithm, API-key comparison. One is left `uncertain —
verify` (R7).

## Phase 1 — Design & Contracts → `data-model.md`, `contracts/`, `quickstart.md`

1. Entities, validation rules and state transitions → `data-model.md` (LogEntry, SignalEvent,
   Bucket, AuditRecord, GovernanceBlock; key grammar from ADR-0068).
2. REST contract → `contracts/openapi-delta.yaml` (five paths); no events, no Avro.
3. Runnable scenarios mirroring AC-01…AC-10 → `quickstart.md`.
4. Constitution Check re-run after design: unchanged (I, IV, VII, VIII remain "justified").

## Observability Design (Article VI)

| Item                | Value                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| CUJ impacted        | "Copilot reads path health" — `POST /ingestion` → `GET /analytics` within 60 s                     |
| New metrics / spans | `gs_ingest_accepted_total`, `gs_ingest_rejected_total`, `gs_queue_depth`, `gs_queue_dropped_total`, `gs_analytics_latency_seconds` (histogram), `gs_governance_hitl_total`; spans `ingestion.batch`, `worker.flush`, `analytics.query` |
| SLO entry           | `docs/sre/slo/golden-signals.yaml` — availability of `/analytics` 99.5%; freshness lag p95 ≤ 60 s  |
| Dashboard / runbook | Grafana "Golden Signals pipeline"; runbook `docs/runbooks/golden-signals.md` (queue drops, store down, HITL storm) |
| Rollback indicator  | `gs_queue_dropped_total` rising or `/analytics/health` 503 for > 2 min after deploy → roll back    |

## Complexity Tracking

| Violation                                        | Why needed                                                                                     | Simpler alternative rejected because                                                  |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `MetricStore` interface + two implementations    | Keeps NFR-05 core-logic tests Redis-free and is the exit seam to a TSDB (ADR-0067)             | Direct Redis calls would force Testcontainers into every unit test and hide the seam |
| Spec still `draft` while plan exists (Article I) | Worked example of the bundle; Phase 6 is blocked by `check-prerequisites.sh --require-approved` | Marking the spec `approved` would be the agent approving its own work (Article V)     |
