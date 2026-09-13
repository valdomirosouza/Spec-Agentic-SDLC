# Data Model: Log-Based Golden Signals

**Spec**: `spec.md` §4 Key Entities | **Plan**: `plan.md` | **Phase**: 5 / Phase 1 design

## Entities

### LogEntry _(inbound, validated at ingestion — FR-01)_

| Field              | Type            | Validation                                         |
| ------------------ | --------------- | -------------------------------------------------- |
| `timestamp`        | integer         | epoch **milliseconds**; required                   |
| `path`             | string          | required; non-empty; ≤ 2 048 chars                 |
| `method`           | string          | required; HTTP method token                        |
| `status_code`      | integer         | 100–599                                            |
| `response_time_ms` | number (float)  | ≥ 0                                                |
| `bytes_sent`       | integer         | ≥ 0                                                |
| `client_ip`        | string          | IPv4 or IPv6; **masked on entry** (FR-02)          |
| `backend_name`     | string          | optional                                           |

Per-entry validation failures count toward `rejected`; a batch that is not a JSON array, or
whose JSON is malformed, is rejected wholesale with `422`.

### SignalEvent _(immutable, one per accepted LogEntry — FR-03)_

`path` (percent-encoded per ADR-0068), `bucket_start_1m`, `bucket_start_5m`, `latency_ms`,
`is_error` (`status_code >= 400`), `is_saturated` (`bytes_sent >= threshold(path)`).

### Bucket _(aggregate per `(path, signal, window, bucket_start)` — FR-05)_

| Field       | Type        | Notes                                                  |
| ----------- | ----------- | ------------------------------------------------------ |
| `count`     | integer     | traffic                                                |
| `sum`       | number      | latency sum                                            |
| `min`/`max` | number      | latency extremes                                       |
| `errors`    | integer     | error count → `error_rate = errors / count`            |
| `saturated` | integer     | saturated-sample count → `saturation_pct`              |
| `samples`   | sorted set  | latency samples for percentile interpolation (FR-07)   |

**State transitions**: `open` (current window, in memory) → `flushed` (persisted on roll-over or
timer) → `expired` (TTL, relative to the newest bucket). A bucket is never mutated after expiry.

### AuditRecord _(append-only — FR-14)_

`ts` (epoch ms), `endpoint`, `hashed_key` (SHA-256 of the API key), `trace_id`, `status` (HTTP).
No update or delete path exists (ADR-0026).

### GovernanceBlock _(attached to analytics responses — FR-12/13)_

```json
{
  "data_classification": "telemetry-L2",
  "pii_sanitized": true,
  "retention_policy": "1m:2h,5m:24h",
  "audit_trail": "/audit",
  "recommended_action_mode": "HOTL",
  "human_approval_required": false
}
```

`recommended_action_mode` ∈ `HOTL | HITL`; flips to `HITL` (and `human_approval_required: true`)
when P99 `>` `HITL_P99_LATENCY_MS` or error rate `>` `HITL_ERROR_RATE` (strict).

## Store key grammar (ADR-0068 §4, verbatim)

```text
gs:{signal}:{path}:{window}:{epoch_bucket}            # hash: count, sum, min, max, errors, saturated
gs:{signal}:{path}:{window}:{epoch_bucket}:samples    # sorted set: latency samples (score = value)
gs:paths                                              # set: every tracked {path}
```

`{signal}` ∈ `traffic|latency|error|saturation`; `{window}` ∈ `1m|5m`; `{epoch_bucket}` is the
integer `bucket_start` in epoch seconds. `{path}` is percent-encoded with the
`encodeURIComponent` algorithm before any key is assembled and decoded only for `/analytics/paths`.

## Retention (ADR-0067 §3)

Every key is written with `EXPIRE`: `RETENTION_1M_SECONDS` (default 7 200) for 1m keys,
`RETENTION_5M_SECONDS` (default 86 400) for 5m keys. Horizons are measured from the newest
ingested bucket so replayed fixtures are not evicted by wall-clock.

## PII classification

| Field       | Class | Masking point                          | Stored form                              |
| ----------- | ----- | -------------------------------------- | ---------------------------------------- |
| `client_ip` | L2    | `IpMasker`, before queueing or logging | IPv4 last octet zeroed; IPv6 last 80 bits zeroed |

No other field is personal data.
