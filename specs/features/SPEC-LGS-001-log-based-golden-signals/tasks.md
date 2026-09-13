<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Tasks: Log-Based Golden Signals

**Input**: `specs/features/SPEC-LGS-001-log-based-golden-signals/` — plan.md (required), spec.md (required), research.md, data-model.md, contracts/
**Phase**: 6 — Development (ADR-0058) | **Branch**: `feature/SPEC-LGS-001-log-based-golden-signals`

<!--
  Produced by /sdd-tasks. Worked example of the bundle (ADR-0090). Tests are NOT optional
  (Constitution II), every task cites the requirement it serves, and each phase declares ≤ 2
  skills (ADR-0060). Phase 6 does not start until spec.md is `approved`
  (check-prerequisites.sh --require-approved) and the two open checklist items are decided.
-->

## Format: `- [ ] [ID] [P?] [Story] Description with exact file path — Refs: FR/AC`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1, US2, US3 (required on user-story phases only)
- **Refs**: the FR-/AC-/NFR- ids the task satisfies (traceability, Constitution VII)
- **Skills**: at most two `skills/…` files per task; a third means the task must be split

## Phase 1: Setup (shared infrastructure)

- [ ] T001 Create branch `feature/SPEC-LGS-001-log-based-golden-signals`; confirm `spec.md` status is `approved` and `checklists/requirements.md` has no undecided item
- [ ] T002 [P] Scaffold `services/golden-signals/` (Java 21, Spring Boot 3.5.x, `pom.xml` with pinned versions and CVE overrides) — Refs: NFR-02, NFR-08
- [ ] T003 [P] Register `golden-signals` in the adopting repository's service registry and CODEOWNERS; add the `gs-redis` Compose profile per ADR-0067 §5 — Refs: NFR-01
- [ ] T004 [P] `.env.example` entries for every variable in plan.md §Configuration — Refs: NFR-04

## Phase 2: Foundational (blocking prerequisites)

**⚠️ No user-story work starts until this phase is complete.**
**Skills**: `skills/domain/domain-modeling.md`, `skills/devsecops/owasp-top10.md`

- [ ] T005 Records `LogEntry`, `SignalEvent`, `Bucket`, `AuditRecord` in `src/main/java/com/yourorg/goldensignals/domain/` per data-model.md — Refs: FR-01, FR-03, FR-05, FR-14
- [ ] T006 [P] STRIDE pass → `specs/security/threat-model-SPEC-LGS-001-golden-signals.md` (ingestion boundary, agent-facing analytics); reviewer ticks CHK011 — Refs: NFR-06, Spec §7
- [ ] T007 [P] `contracts/openapi-delta.yaml` merged into the published OpenAPI document; controller stubs generated, not hand-written — Refs: FR-01, FR-07…FR-14
- [ ] T008 [P] `TraceIdFilter` + structured JSON logging config (`X-Trace-Id` read or generated) in `api/` — Refs: NFR-03
- [ ] T009 `MetricStore` interface + `InMemoryMetricStore` in `infra/` (persist, query, trackedPaths, ping) — Refs: FR-05, FR-06, FR-09

**Checkpoint**: foundation ready; stories may proceed in parallel.

## Phase 3: User Story 1 — Privacy-safe percentiles per path (Priority: P1) 🎯 MVP

**Goal**: post a batch, get masked, aggregated P50/P95/P99 per path within one window.
**Independent Test**: quickstart scenarios 2–4 and 8 pass on the in-memory profile.
**Skills**: `skills/privacy/pii.md`, `skills/observability/otel-instrumentation.md`

### Tests first (write, run, watch them FAIL)

- [ ] T010 [P] [US1] `PercentileCalculatorTest` against `src/test/resources/percentiles-reference.json` with `requirement("SPEC-LGS-001/FR-07")` — Refs: AC-06
- [ ] T011 [P] [US1] `IpMaskerTest` (IPv4 last octet, IPv6 last 80 bits, compressed `::`, idempotent, malformed never persisted) — Refs: FR-02, AC-03
- [ ] T012 [P] [US1] `SignalExtractorTest` + `WindowBucketerTest` (error iff `>= 400`, saturation `>=` with per-path override, left-closed/right-open, 1m and 5m each once) — Refs: FR-03, FR-05
- [ ] T013 [P] [US1] `MalformedBatchTest` (non-array / wrong type / missing field ⇒ 422, nothing persisted) — Refs: FR-01, AC-02
- [ ] T014 [P] [US1] `PipelineIntegrationTest` (seed ~1k over ≥ 5 paths → drain → query; error rate ±2%; retention evicts old buckets) — Refs: FR-04, FR-05, FR-06, AC-04, AC-10
- [ ] T015 [P] [US1] `PathsIntegrationTest`, `HealthIntegrationTest` (store down ⇒ 503) — Refs: FR-08, FR-09, AC-01, AC-05
- [ ] T016 [P] [US1] `PiiLeakTest` (store dump + captured logs contain no unmasked octet/hextet) — Refs: FR-02, AC-03

### Implementation

- [ ] T017 [P] [US1] `IpMasker` in `domain/` — Refs: FR-02
- [ ] T018 [P] [US1] `WindowBucketer`, `SignalExtractor`, `Aggregate`, `PercentileCalculator` in `domain/` (no Spring, no stats library) — Refs: FR-03, FR-05, FR-07
- [ ] T019 [US1] `IngestQueue` (bounded `ArrayBlockingQueue`, non-blocking `offer`, drop counter) + `AggregationWorker` (virtual thread, flush on roll-over/timer/shutdown) in `queue/` (depends on T018) — Refs: FR-04, FR-05, NFR-02
- [ ] T020 [US1] `IngestionController` (validation → mask → extract → offer; 202 with counts; 422 on malformed batch) + `GlobalExceptionHandler` (no PII or stack in bodies) — Refs: FR-01, FR-02
- [ ] T021 [US1] `AnalyticsController` (`/analytics`, `/analytics/paths`, `/analytics/health`; 422 on missing path or bad enum) — Refs: FR-07, FR-08, FR-09
- [ ] T022 [US1] `RedisMetricStore` (Lettuce, key grammar and RFC 3986 encoder per ADR-0068, `EXPIRE` per window) + `RedisStoreContractTest` parity with the in-memory store — Refs: FR-05, FR-06
- [ ] T023 [US1] Metrics and spans from plan.md Observability Design (`gs_ingest_*`, `gs_queue_*`, `gs_analytics_latency_seconds`; spans `ingestion.batch`, `worker.flush`, `analytics.query`) — Refs: NFR-03, SC-01, SC-04

**Checkpoint**: US1 fully functional and independently testable (quickstart 2–4, 8).

## Phase 4: User Story 2 — Authenticated, rate-limited and audited access (Priority: P2)

**Goal**: only key-holders ingest or query; floods are throttled; every call is audited.
**Independent Test**: quickstart scenarios 5 and 7 pass.
**Skills**: `skills/devsecops/owasp-top10.md`, `skills/api/rest-api-design.md`

### Tests first (write, run, watch them FAIL)

- [ ] T024 [P] [US2] `AuthTest` (missing/invalid key ⇒ 401 on four paths; health needs none; constant-time compare) — Refs: FR-10, AC-07
- [ ] T025 [P] [US2] `RateLimitTest` (601st call in 60 s ⇒ 429 + `Retry-After`) — Refs: FR-11, AC-07
- [ ] T026 [P] [US2] `AuditIntegrationTest` (`/audit?limit=N` returns last N with SHA-256 hashed key and trace id; no raw key anywhere) — Refs: FR-14, AC-09
- [ ] T027 [P] [US2] `KeyInjectionTest` (path with `:`, `*`, newline, `gs:` prefix cannot collide with another path's keys) — Refs: FR-03, ADR-0068

### Implementation

- [ ] T028 [P] [US2] `ApiKeyFilter` (`GS_API_KEYS`, `MessageDigest.isEqual`) in `api/` — Refs: FR-10
- [ ] T029 [P] [US2] `RateLimiter` sliding window per hashed key on `POST /ingestion` (resolve research.md R7 first) — Refs: FR-11
- [ ] T030 [US2] `AuditStore` (append-only) + `AuditController`; every ingestion/analytics call recorded via a filter (depends on T028) — Refs: FR-14
- [ ] T031 [US2] Abuse-case tests mirrored into the adopting repository's `tests/abuse_cases/` markers; count must not decrease (ADR-0050) — Refs: NFR-06

**Checkpoint**: US2 independently testable; Security Lead approval if any HIGH finding (Phase 9).

## Phase 5: User Story 3 — Governance block and HITL flip (Priority: P3)

**Goal**: every analytics answer carries `_governance`; breaches flip to HITL.
**Independent Test**: quickstart scenario 6 passes both ways.
**Skills**: `skills/ai/guardrails.md`, `skills/ethics/ethical-ai-review.md`

### Tests first (write, run, watch them FAIL)

- [ ] T032 [P] [US3] `GovernanceEvaluatorTest` (exactly-at-threshold is not a flip; one tick over flips; both thresholds) — Refs: FR-13, AC-08
- [ ] T033 [P] [US3] `SignalPoisoningTest` (a flood of high-latency entries flips to HITL, never silently HOTL) — Refs: FR-13, AC-08
- [ ] T034 [P] [US3] `GovernanceBlockTest` (`_governance` present on every analytics response with the six fields and exact wire values) — Refs: FR-12

### Implementation

- [ ] T035 [US3] `GovernanceEvaluator` in `domain/` + decorator in `AnalyticsController` — Refs: FR-12, FR-13
- [ ] T036 [US3] `gs_governance_hitl_total` counter + AI-safety checklist entry (Phase 10 mandatory per plan.md) — Refs: NFR-03, Spec §7

**Checkpoint**: US3 independently testable; AI governance approval (Phase 10).

## Phase 6: Polish & Cross-Cutting

- [ ] T037 [P] `docs/sre/slo/golden-signals.yaml`, Grafana dashboard, `docs/runbooks/golden-signals.md` per plan.md Observability Design — Refs: NFR-07, SC-01
- [ ] T038 [P] RIPD entry under `docs/privacy/ripd/`; DPO decides A2 and ticks CHK008 — Refs: Spec §7
- [ ] T039 [P] Dependency manifest entry + SBOM for `services/golden-signals` — Refs: NFR-08
- [ ] T040 Spec frontmatter: fill `implemented_by`, `verified_by`; `issue`; status → `implemented` at merge — Refs: Constitution VII
- [ ] T041 Run quickstart.md scenarios 1–8 end to end on the `redis` profile and attach the output to the PR — Refs: AC-01…AC-10

## Dependencies & Execution Order

- Setup → Foundational (blocks all stories) → US1 → US2 and US3 (may run in parallel after US1) → Polish
- Within a story: tests → domain → queue/store → controllers → observability
- Tasks touching the same file run sequentially (T019 after T018; T030 after T028; T035 after T021)

## Implementation Strategy

1. **MVP first**: Setup + Foundational + User Story 1 → STOP, validate with quickstart 2–4 and 8, demo.
2. **Incremental**: US2 hardens the boundary; US3 adds governance; each adds value without breaking US1.
3. **Scope per run**: `/sdd-implement only phase 1-2`, then `only US1`, then `only US2`, then
   `only US3`, then `only phase 6` — each run fits one context window.

## Human gates touched by these tasks

- [ ] Spec approval (`draft` → `approved`, Spec-as-PR: Tech Lead + Security Lead) — before T001
- [ ] Code review approval (Phase 7) — required before merge
- [ ] Security approval if any HIGH/CRITICAL finding (Phase 9) — after US2
- [ ] AI governance approval (Phase 10, mandatory: agent-facing HITL guidance) — after US3
- [ ] PRR sign-off (Phase 11) — after T037
