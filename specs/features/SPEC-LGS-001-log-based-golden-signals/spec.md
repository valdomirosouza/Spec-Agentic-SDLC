---
id: SPEC-LGS-001
kind: feature-spec
status: approved # draft | in-review | approved | implemented | superseded (ADR-0085)
owner: valdomirosouza
issue: null
governing_adrs:
  - ADR-0003
  - ADR-0011
  - ADR-0012
  - ADR-0020
  - ADR-0025
  - ADR-0026
  - ADR-0029
  - ADR-0066
  - ADR-0067
  - ADR-0068
  - ADR-0069
new_adrs_required: []
implemented_by: [] # filled at Phase 6
verified_by: [] # tests that prove the acceptance criteria
related_specs:
  - specs/system/SPEC-LGS-001-log-based-golden-signals.md
  - specs/security/threat-model.md
roadmap: null
last_updated: 2026-09-13
---

# Feature Specification: Log-Based Golden Signals — ingestion and percentile analytics

**Input**: "Ingest HAProxy access logs, mask client IPs at the door, aggregate the four Golden
Signals per path into 1-minute and 5-minute windows, and serve P50/P95/P99 per bucket with a
governance block the agentic copilot can act on."
**Risk class**: high _(untrusted ingestion boundary, PII at the edge, agent-facing output)_

<!--
  Worked example of the specs/features/<SPEC-ID>-<slug>/ bundle (ADR-0090). Derived from the
  system spec specs/system/SPEC-LGS-001-log-based-golden-signals.md (14 FR / 8 NFR / 10 AC) and
  the /deliver dry-run archived under docs/sdlc/deliver-example/. Stack, components and keys
  live in plan.md, not here.
-->

## Clarifications

### Session 2026-09-12

- Q: Which percentile method does FR-07 mean by "rank-based interpolation"? → A: Linear
  interpolation between closest ranks, `h = (n − 1) · p / 100` over the ascending samples
  (NumPy default, Excel `PERCENTILE.INC`). Empty set ⇒ `null`; single sample ⇒ that value.
- Q: Boundary conventions? → A: saturation `bytes_sent >=` threshold; error `status_code >= 400`;
  the FR-13 HITL flip is **strict** `>`. Windows are epoch-aligned, left-closed / right-open.
- Q: Is the concurrency mechanism (asyncio task, virtual thread, event loop) part of the spec? →
  A: No. The binding requirement is the **property**: bounded in-process queue, non-blocking
  producer, asynchronous consumer, flush on shutdown. The mechanism lives in the per-language ADR.
- Q: `timestamp` encoding? → A: integer epoch milliseconds, not ISO-8601.
- Q: Retention clock origin? → A: relative to the most recent ingested bucket, so replayed
  historical fixtures are not evicted by wall-clock; a production backend may add wall-clock TTLs.
- Q: Open questions §15 of the system spec (queue, single-node store, saturation threshold,
  topology)? → A: resolved by ADR-0069, ADR-0067, ADR-0068 and plan.md §Structure Decision.

## 1. Context & Problem

### 1.1 Problem statement

An agentic AI copilot that reasons about service health needs tail-latency (P95/P99), error
rate, traffic and saturation per path in near real time. Today those signals exist only as raw
HAProxy access logs: unaggregated, containing client IPs, and without any statement of how far
an agent may act on them without a human.

### 1.2 Why now

The copilot is moving from read-only advice to recommended actions (ADR-0011). Without
privacy-safe, auditable, governance-labelled signals, every recommendation either leaks PII or
cannot be trusted by the HITL reviewer.

## 2. User Scenarios & Testing _(mandatory)_

### User Story 1 — Privacy-safe percentiles per path (Priority: P1) 🎯 MVP

An SRE (or the copilot) posts a batch of access-log entries and, within one aggregation window,
queries P50/P95/P99 latency, error rate, traffic and saturation for any path, with no client IP
ever stored or logged.

**Why this priority**: it is the whole value proposition; auth, audit and governance only make
sense once the numbers exist.

**Independent Test**: seed ~1 000 synthetic entries over ≥ 5 paths, query
`/analytics?path=…&signal=latency&window=1m`, assert non-empty numeric percentiles and that no
unmasked IP appears in the store dump or logs.

**Acceptance Scenarios**:

1. **Given** a well-formed batch, **When** it is posted to `/ingestion`, **Then** the reply is
   `202` with `accepted`/`rejected` counts and every entry's `client_ip` is masked before any
   persistence or log write.
2. **Given** a malformed batch, **When** posted, **Then** the reply is `422` and nothing is persisted.
3. **Given** seeded traffic, **When** `/analytics` is queried for a path, signal and window,
   **Then** each bucket carries P50/P95/P99, count, error_rate and saturation_pct, and
   `/analytics/paths` lists every seeded path.
4. **Given** a retention policy of `1m:2h, 5m:24h`, **When** the horizon passes relative to the
   newest bucket, **Then** older buckets are no longer returned.

### User Story 2 — Authenticated, rate-limited and audited access (Priority: P2)

A platform owner can prove that only key-holders ingest or query, that a flooding key is
throttled, and that every call is in an immutable audit trail.

**Why this priority**: the ingestion boundary is untrusted and the analytics surface is consumed
by an autonomous agent; both need evidence of control before production.

**Independent Test**: call each endpoint without a key (expect `401`, except health), exceed the
per-key limit (expect `429` + `Retry-After`), then read `/audit?limit=N` and find the calls with
hashed keys and trace ids.

**Acceptance Scenarios**:

1. **Given** no or an invalid API key, **When** `/ingestion`, `/analytics` or `/audit` is called,
   **Then** the reply is `401`; `/analytics/health` answers without a key.
2. **Given** a key exceeding its sliding-window quota, **When** it posts again, **Then** the reply
   is `429` with `Retry-After`.
3. **Given** any ingestion or analytics call, **When** it completes, **Then** an audit record
   (timestamp, endpoint, hashed key, trace id, status) exists and is readable via `/audit`.

### User Story 3 — Governance block and HITL flip (Priority: P3)

The copilot reads a `_governance` block on every analytics answer and, when P99 latency or error
rate breach the configured thresholds, is told to seek human approval instead of acting.

**Why this priority**: it turns the data into governed autonomy (ADR-0011); it depends on P1
numbers and P2 audit pointers.

**Independent Test**: seed high-latency data, query analytics, assert
`recommended_action_mode == "HITL"` and `human_approval_required == true`; seed normal data and
assert `HOTL` / `false`.

**Acceptance Scenarios**:

1. **Given** normal traffic, **When** analytics is queried, **Then** `_governance` reports
   `data_classification: telemetry-L2`, `pii_sanitized: true`, the retention policy, the audit
   pointer, `HOTL` and `human_approval_required: false`.
2. **Given** P99 strictly above `HITL_P99_LATENCY_MS` or error rate strictly above
   `HITL_ERROR_RATE`, **When** analytics is queried, **Then** the mode is `HITL` and approval is
   required.

### Edge Cases

- Empty bucket (no samples): omitted from `buckets`; summary fields are `null`, never an error.
- Single-sample bucket: P50 = P95 = P99 = that sample; no division by zero.
- A sample timestamped exactly at a bucket end belongs to the **next** bucket.
- IPv6 addresses in compressed `::` form are normalised before the last 80 bits are zeroed.
- Value exactly at a HITL threshold does **not** flip; one tick above does.
- Queue full: the entry is counted as `rejected`, a drop counter increments, ingestion still `202`.
- One entry updates its 1m and its 5m bucket exactly once each.
- `signal` or `window` outside the enumerations ⇒ `422`, not `500`.
- Store unreachable ⇒ `/analytics/health` `503` with `redis_connected: false`; other endpoints
  fail explicitly, never with a hidden retry loop.

## 3. Non-Goals / Out of Scope

- The copilot itself, its planner or any LLM inference (a consumer, not built here).
- Anomaly detection or forecasting over the time series.
- Distributed-tracing ingestion (logs → Golden Signals only).
- Long-horizon storage (Redis-only by design; exit path recorded in ADR-0067).
- Multi-tenant scaling and HA store clustering (single node in the initial scope).

## 4. Functional Requirements _(mandatory)_

| ID    | Requirement (EARS: WHEN … the system SHALL …)                                                                                                                                                | Story | Priority |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------- |
| FR-01 | WHEN a JSON array of log entries is posted to `/ingestion`, the system SHALL validate each entry against the published schema, answer `202` with `accepted`/`rejected` counts, and answer `422` when the batch itself is malformed. | US1   | must     |
| FR-02 | WHEN an entry is accepted, the system SHALL mask `client_ip` (IPv4 last octet, IPv6 last 80 bits) before any field is persisted or logged.                                                  | US1   | must     |
| FR-03 | WHEN an entry is accepted, the system SHALL derive the four Golden Signals for its `(path, window)` per §8.                                                                                  | US1   | must     |
| FR-04 | WHEN signals are extracted, the system SHALL hand them to a bounded internal queue with a non-blocking producer so that ingestion never waits on processing.                                 | US1   | must     |
| FR-05 | WHILE events are queued, the system SHALL aggregate them into 1-minute and 5-minute epoch-aligned windows computing count, sum, min, max and the latency sample set per `(path, signal, window)`. | US1   | must     |
| FR-06 | WHEN an aggregate is persisted, the system SHALL apply the configurable retention policy (default `1m:2h`, `5m:24h`) measured from the newest ingested bucket.                              | US1   | must     |
| FR-07 | WHEN `/analytics?path=&signal=&window=&from=&to=` is requested, the system SHALL return P50/P95/P99 per bucket (linear interpolation between closest ranks) plus a summary; `path` is required and invalid enums answer `422`. | US1   | must     |
| FR-08 | WHEN `/analytics/paths` is requested, the system SHALL list every currently tracked path.                                                                                                    | US1   | must     |
| FR-09 | WHEN `/analytics/health` is requested, the system SHALL report store connectivity and tracked-path count, answering `503` when the store is down.                                            | US1   | must     |
| FR-10 | WHEN `/ingestion`, `/analytics`, `/analytics/paths` or `/audit` is called without a valid API key, the system SHALL answer `401`; `/analytics/health` SHALL need no key.                    | US2   | must     |
| FR-11 | WHEN a key exceeds its sliding-window ingestion quota, the system SHALL answer `429` with a `Retry-After` header.                                                                             | US2   | must     |
| FR-12 | WHEN an analytics response is produced, the system SHALL attach a `_governance` block (data_classification, pii_sanitized, retention_policy, audit_trail, recommended_action_mode, human_approval_required). | US3   | must     |
| FR-13 | WHEN P99 latency is strictly above `HITL_P99_LATENCY_MS` or error rate strictly above `HITL_ERROR_RATE`, the system SHALL set `recommended_action_mode: HITL` and `human_approval_required: true`. | US3   | must     |
| FR-14 | WHEN any ingestion or analytics call completes, the system SHALL append an immutable audit record (timestamp, endpoint, hashed key, trace id, status) and expose the last N via `/audit?limit=`. | US2   | must     |

### Key Entities

- **LogEntry**: one HAProxy access-log line — `timestamp` (epoch ms), `path`, `method`,
  `status_code`, `response_time_ms`, `bytes_sent`, `client_ip` (masked on entry), optional
  `backend_name`.
- **SignalEvent**: the four signals derived from one LogEntry for its `(path, window)`.
- **Bucket**: the aggregate for `(path, signal, window, bucket_start)` — count, sum, min, max,
  errors, saturated, latency samples.
- **AuditRecord**: `ts`, `endpoint`, `hashed_key`, `trace_id`, `status`; append-only.
- **GovernanceBlock**: the `_governance` object attached to analytics responses.

## 5. Non-Functional Requirements

| ID     | Requirement                                                                                                                   | Category (taxonomy) | Evidence / gate                        |
| ------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------- |
| NFR-01 | All services containerised and orchestrated on a shared network.                                                              | Operability         | AC-01, quickstart.md                   |
| NFR-02 | Ingestion is decoupled from processing by a bounded in-process queue, non-blocking producer, asynchronous consumer, flush on shutdown; the mechanism is fixed per language in an ADR (ADR-0066/0069). | Performance         | AC-10, plan.md                         |
| NFR-03 | Structured JSON logging; `X-Trace-Id` propagated or generated.                                                                 | Observability       | log sample in quickstart.md            |
| NFR-04 | All configuration via environment variables with documented defaults.                                                         | Operability         | plan.md §Configuration                 |
| NFR-05 | Unit coverage ≥ 80% on percentiles, masking, extraction; one full-pipeline integration test.                                   | Quality             | Phase 8 coverage gate                  |
| NFR-06 | Every store access handles connection/timeout errors explicitly; no hidden global state.                                      | Reliability         | AC-01 store-down path                  |
| NFR-07 | `/analytics` latency budget documented and suitable for incident-time queries (target p95 ≤ 300 ms at 24 h of 5m buckets).    | Performance         | SC-04                                  |
| NFR-08 | Dependency versions pinned; dependency manifest and SBOM produced per build.                                                   | Security            | Phase 9 SBOM                           |

PII: `client_ip` is the only personal field (L2 — see §7). No other PII enters the system.

## 6. Success Criteria _(mandatory, measurable, technology-agnostic)_

| ID    | Measurable outcome                                                                                       | Measurement                                        |
| ----- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| SC-01 | Percentiles for a path are queryable within one aggregation window (≤ 60 s) of ingestion.                | Freshness lag SLI from quickstart scenario 3       |
| SC-02 | Zero unmasked client IPs in the store or logs after ingesting a known-IP fixture.                         | AC-03 scan                                         |
| SC-03 | 100% of ingestion/analytics calls have an audit record with a hashed key and trace id.                    | AC-09 count equals request count                   |
| SC-04 | `GET /analytics` answers within 300 ms p95 over 24 h of 5-minute buckets for one path.                    | NFR-07 measurement in quickstart scenario 3        |
| SC-05 | Threshold breaches flip the governance mode to HITL in 100% of seeded breach cases.                       | AC-08                                              |

## 7. Governance, Privacy & Security _(gate: threat & privacy review)_

| Concern                                  | Control in this spec                                                                      | Maps to                        |
| ---------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------ |
| Human oversight (HITL/HOTL)              | `_governance` block; HITL flip on threshold breach (FR-12/13); the copilot never bypasses it | ADR-0011                       |
| PII (classify L1–L4; mask at boundaries) | `client_ip` = **L2** (network identifier); masked at ingestion before any write (FR-02)     | ADR-0012, specs/privacy/       |
| DPIA / RIPD required?                    | RIPD entry: yes (new processing of masked network identifiers). Full DPIA: decision pending DPO at the Discovery gate | docs/privacy/dpia/             |
| Auditability (immutable trail)           | Append-only audit records with hashed keys (FR-14); `/audit` read-only                     | ADR-0026                       |
| Authn / abuse (auth, rate limit)         | API key (constant-time compare) on all but health; sliding-window rate limit (FR-10/11); STRIDE pass over the ingestion boundary pending | specs/security/threat-model.md |
| OWASP controls touched                   | ASVS V2 authn, V4 access control, V5 input validation, V7 logging; LLM Top 10 LLM08 (agent action guarded by HITL) | specs/security/*.yaml          |
| Cost                                     | Bounded queue, single store, TTL-bounded memory                                            | ADR-0020                       |

## 8. Golden Signals & SLO _(gate: observability)_

| Signal     | Derivation                                                     | Exposed as                         |
| ---------- | -------------------------------------------------------------- | ---------------------------------- |
| Traffic    | Request count per `(path, window)`                             | `count` per bucket                 |
| Latency    | `response_time_ms` samples per window                          | P50 / P95 / P99 per bucket         |
| Errors     | `status_code >= 400`                                           | `error_rate = errors / count`      |
| Saturation | `bytes_sent >= SATURATION_BYTES_THRESHOLD` (per-path override) | `saturation_pct`                   |

SLOs for this system itself (availability of `/analytics`, freshness lag ≤ 60 s) are declared in
`docs/sre/slo/` by the plan's Observability Design.

## 9. Acceptance Criteria _(gate: canonical, machine-traceable)_

| ID    | Given / When / Then (one line)                                                                                  | Covers FR(s)         | Verified by (test path or `requirement` marker)                |
| ----- | --------------------------------------------------------------------------------------------------------------- | -------------------- | -------------------------------------------------------------- |
| AC-01 | Given the stack is up, when health is called, then `200` with `redis_connected` and `tracked_paths`; store down ⇒ `503` | FR-09                | `HealthIntegrationTest` — `requirement("SPEC-LGS-001/FR-09")`  |
| AC-02 | Given a malformed batch, when posted, then `422` and nothing persisted; a valid batch ⇒ `202` with counts        | FR-01                | `MalformedBatchTest` — `requirement("SPEC-LGS-001/FR-01")`     |
| AC-03 | Given a fixture with known IPs, when ingested, then no unmasked octet/hextet in store dump or logs               | FR-02                | `IpMaskerTest`, `PiiLeakTest` — `requirement("SPEC-LGS-001/FR-02")` |
| AC-04 | Given ~1k entries over ≥ 5 paths, when latency/1m is queried, then non-empty numeric P50/P95/P99 per bucket      | FR-03, FR-05, FR-07  | `PipelineIntegrationTest` — `requirement("SPEC-LGS-001/FR-07")` |
| AC-05 | Given seeded paths, when `/analytics/paths` is called, then every seeded path is listed                          | FR-08                | `PathsIntegrationTest` — `requirement("SPEC-LGS-001/FR-08")`   |
| AC-06 | Given a known dataset, when percentiles are computed, then they equal the reference values byte for byte         | FR-07                | `PercentileCalculatorTest` — `requirement("SPEC-LGS-001/FR-07")` |
| AC-07 | Given no key, when protected endpoints are called, then `401`; given quota exceeded, then `429` + `Retry-After`  | FR-10, FR-11         | `AuthTest`, `RateLimitTest` — `requirement("SPEC-LGS-001/FR-10")` |
| AC-08 | Given high-latency seed data, when analytics is queried, then mode `HITL` and `human_approval_required: true`   | FR-12, FR-13         | `GovernanceEvaluatorTest`, `SignalPoisoningTest` — `requirement("SPEC-LGS-001/FR-13")` |
| AC-09 | Given N prior calls, when `/audit?limit=N` is read, then the last N records with hashed keys are returned        | FR-14                | `AuditIntegrationTest` — `requirement("SPEC-LGS-001/FR-14")`   |
| AC-10 | Given the full pipeline (seed → queue → aggregate → persist → query), when run end to end, then exit `0` and error rate within ±2% of the injected rate; buckets older than retention are gone | FR-04, FR-05, FR-06 | `PipelineIntegrationTest`, `RedisStoreContractTest` — `requirement("SPEC-LGS-001/FR-04")` |

## 10. Requirement Coverage _(gate)_

**Coverage footer.** _14_ FRs total · _14_ mapped to ≥ 1 AC · **_0_ unmapped** (K must be 0 for DoR/DoD)

## 11. Risks & Limitations

- **Retention horizon.** A single in-memory store bounds historical depth; the exit path to a
  dedicated time-series database is recorded as an ADR-0067 consequence.
- **Saturation is a proxy.** `bytes_sent` approximates resource saturation; the governance block
  makes no claim of exact resource use (ADR-0068).
- **Window boundaries split bursts.** Mitigated by the pinned left-closed / right-open rule; the
  5-minute window smooths what the 1-minute window splits.

## 12. Open Questions

None. The four open questions of the system spec §15 are resolved (see Clarifications).

## 13. Assumptions

| #   | Assumption                                                                          | Owner         | Resolve by (phase)   | Status (open / confirmed / rejected) |
| --- | ----------------------------------------------------------------------------------- | ------------- | -------------------- | ------------------------------------ |
| A1  | HAProxy is the only log source in the initial scope; other sources reuse the schema. | Tech Lead     | 4 — Specification    | confirmed                            |
| A2  | A masked IP (L2) does not require a full DPIA; a RIPD entry suffices.                | DPO           | 2 — Discovery        | open                                 |
| A3  | Single-node store availability is acceptable for the initial, internal deployment.   | SRE Lead      | 5 — Architecture     | confirmed (ADR-0067)                 |

## 14. References

- System spec: `specs/system/SPEC-LGS-001-log-based-golden-signals.md` (§16 lists the literature).
- Dry-run delivery evidence: `docs/sdlc/deliver-example/`.
- ADR-0066 (runtime stack), ADR-0067 (store), ADR-0068 (extraction rules), ADR-0069 (queue).
