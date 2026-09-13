# Research: Log-Based Golden Signals

**Spec**: `spec.md` | **Plan**: `plan.md` | **Phase**: 5 / Phase 0 research (ADR-0058)

One entry per unknown, dependency or integration named in the plan's Technical Context. Each
claim is grounded down the chain codebase → specs/docs → Context7 → web → `uncertain — verify`
(Constitution IX).

## R1 — Queue between ingestion and processing (FR-04, NFR-02)

- **Decision**: in-JVM bounded `ArrayBlockingQueue<SignalEvent>` (capacity `INGEST_QUEUE_CAPACITY`,
  default 10 000), non-blocking `offer()` producer, single virtual-thread `take()` consumer.
- **Rationale**: the spec binds the *property* (bounded, non-blocking producer, async consumer,
  flush on shutdown), not the mechanism; Loom makes a blocking consumer cheap; the bound is the
  backpressure (ADR-0020).
- **Alternatives considered**: Redis Streams (rejected as a queue by ADR-0003; Redis stays a
  store only); Kafka (recorded as the scale-out seam, not needed at single-node scope).
- **Grounded in**: ADR-0069, ADR-0003.

## R2 — Time-series store (FR-05, FR-06)

- **Decision**: single-node Redis behind a `MetricStore` interface; hash per bucket, sorted set
  per bucket for latency samples, `gs:paths` set; TTL via `EXPIRE` from
  `RETENTION_1M_SECONDS` / `RETENTION_5M_SECONDS`.
- **Rationale**: no sweep job, memory bounded by TTL, interface is the exit seam to a TSDB.
- **Alternatives considered**: InfluxDB / TimescaleDB (documented exit path; more operational
  surface than the initial scope justifies); the shared dev Redis (rejected — couples workloads
  and persists ephemeral telemetry).
- **Grounded in**: ADR-0067 (including the dedicated, ephemeral `gs-redis` instance).

## R3 — Extraction rules, window semantics, key grammar (FR-03, FR-05, FR-07)

- **Decision**: rules verbatim from ADR-0068 — traffic `count += 1`; latency sample append; error
  iff `status_code >= 400`; saturated iff `bytes_sent >= threshold` (1 MiB default, per-path
  override); windows 1m/5m epoch-aligned, left-closed / right-open; keys
  `gs:{signal}:{path}:{window}:{epoch_bucket}` with `{path}` percent-encoded using the
  `encodeURIComponent` algorithm (every byte outside RFC 3986 unreserved).
- **Rationale**: determinism across services and languages; the encoding rule is the
  key-injection defence.
- **Alternatives considered**: `java.net.URLEncoder` (form encoding, diverges on space and `*`) —
  rejected; a hand-rolled RFC 3986 encoder is required in Java.
- **Grounded in**: ADR-0068 §1–§4.

## R4 — Deployment topology

- **Decision**: one Spring Boot deployable, `services/golden-signals`, four in-JVM modules.
- **Rationale**: NFR-01 and the ADR-0020 cost envelope; the queue and store interfaces keep the
  logical decomposition of the system spec §7.
- **Alternatives considered**: four micro-deployables (more infra, no functional gain at this
  scope); standalone repository (system spec §1.4 chose `monorepo-services`).
- **Grounded in**: system spec §1.4, the superseded feature-spec §0.

## R5 — Percentile method (FR-07, AC-06)

- **Decision**: linear interpolation between closest ranks, `h = (n − 1) · p / 100`, over the
  ascending sorted samples; empty ⇒ `null`; one sample ⇒ that value. No external statistics
  library.
- **Rationale**: two independent implementations must agree byte for byte (AC-06); this is the
  NumPy default and Excel `PERCENTILE.INC`.
- **Alternatives considered**: nearest-rank (cheaper, but disagrees with the reference dataset);
  a stats library (forbidden by FR-07).
- **Grounded in**: spec Clarifications; system spec §10.

## R6 — Runtime stack

- **Decision**: Java 21 / Spring Boot 3.5.x with `spring.threads.virtual.enabled=true`.
- **Rationale**: ADR-0066 overrides the original FastAPI mandate for this service; the 3.5 line
  is kept for the CVE overrides pinned in `pom.xml` (fail-forward).
- **Alternatives considered**: Python/FastAPI (original NFR-02 wording; superseded by ADR-0066).
- **Grounded in**: ADR-0066, system spec NFR-02.

## R7 — Rate-limiter algorithm (FR-11)

- **Decision**: per-hashed-key sliding-window counter held in JVM memory, window 60 s, limit
  `RATE_LIMIT_PER_MINUTE`; `Retry-After` = seconds until the oldest counted request leaves the window.
- **Rationale**: single node, no shared state needed; the audit trail already hashes the key.
- **Alternatives considered**: token bucket (smoother, but the spec names a sliding window);
  Redis-backed limiter (needed only when the service scales out).
- **Status**: `uncertain — verify` whether Spring Boot 3.5 ships a supported rate-limiting filter
  that satisfies the sliding-window wording; if not, implement in `RateLimiter` directly.

## R8 — API-key handling (FR-10, FR-14)

- **Decision**: keys from `GS_API_KEYS`; comparison via `MessageDigest.isEqual` (constant time);
  audit records store a SHA-256 hash of the key, never the key.
- **Rationale**: timing-safe comparison (ASVS V2); the audit trail must not become a credential store.
- **Alternatives considered**: JWT (overkill for machine-to-machine ingestion at this scope).
- **Grounded in**: CLAUDE.md §3.2 (A02, A07), system spec §11.
