# Quickstart: Log-Based Golden Signals

**Spec**: `spec.md` | **Plan**: `plan.md` | **Phase**: 5 / Phase 1 design → executed at Phase 6 and 8

Runnable validation scenarios, one per acceptance criterion. Each states prerequisites, the
command, and the expected outcome. No implementation bodies here.

## Prerequisites

```bash
export GS_API_KEYS=dev-key-1
export SPRING_PROFILES_ACTIVE=redis          # omit for the in-memory store
docker compose --profile golden-signals up -d  # gs-redis + golden-signals
export GS=http://localhost:8080
```

## Scenario 1 — Health (AC-01, FR-09)

```bash
curl -s $GS/analytics/health
# → 200 {"status":"UP","redis_connected":true,"tracked_paths":0}
docker compose stop gs-redis && curl -s -o /dev/null -w '%{http_code}\n' $GS/analytics/health
# → 503 ; then: docker compose start gs-redis
```

## Scenario 2 — Ingestion, validation and masking (AC-02, AC-03, FR-01, FR-02)

```bash
curl -s -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -H 'Content-Type: application/json' \
  -d '[{"timestamp":1757635200000,"path":"/checkout","method":"POST","status_code":200,
        "response_time_ms":123.4,"bytes_sent":5120,"client_ip":"203.0.113.42"}]'
# → 202 {"accepted":1,"rejected":0}
curl -s -o /dev/null -w '%{http_code}\n' -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -d '{"not":"an array"}'
# → 422
docker compose exec gs-redis redis-cli --scan | xargs -n1 docker compose exec -T gs-redis redis-cli dump | grep -c '203.0.113.42'
# → 0   (only 203.0.113.0 may appear)
docker compose logs golden-signals | grep -c '203.0.113.42'
# → 0
```

## Scenario 3 — Seed and query percentiles (AC-04, AC-05, AC-10, SC-01, SC-04, FR-03…FR-08)

```bash
scripts/seed.sh --entries 1000 --paths 5 --error-rate 0.04 | curl -s -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -d @-
sleep 60   # one aggregation window (SC-01)
curl -s "$GS/analytics?path=/checkout&signal=latency&window=1m" -H "X-API-Key: $GS_API_KEYS"
# → 200 {"buckets":[{"bucket_start":1757635200,"p50":…,"p95":…,"p99":…,"count":…,"error_rate":…,"saturation_pct":…}],"summary":{…},"_governance":{…}}
curl -s "$GS/analytics/paths" -H "X-API-Key: $GS_API_KEYS"
# → 200 ["/checkout","/cart","/login","/search","/health"]
curl -s -w '\n%{time_total}\n' "$GS/analytics?path=/checkout&signal=latency&window=5m" -H "X-API-Key: $GS_API_KEYS" | tail -1
# → ≤ 0.300 (SC-04)
```

Expected: `summary.error_rate` within ±0.02 of 0.04; every seeded path listed.

## Scenario 4 — Percentile reference dataset (AC-06)

Unit test `PercentileCalculatorTest` compares against the fixture
`src/test/resources/percentiles-reference.json` (values computed with NumPy's default method).
`mvn -pl services/golden-signals test -Dtest=PercentileCalculatorTest` → green.

## Scenario 5 — Auth and rate limit (AC-07, FR-10, FR-11)

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$GS/analytics/paths"                         # → 401
curl -s -o /dev/null -w '%{http_code}\n' "$GS/analytics/paths" -H 'X-API-Key: wrong'   # → 401
for i in $(seq 1 601); do curl -s -o /dev/null -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -d '[]'; done
curl -s -D - -o /dev/null -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -d '[]' | grep -E '^(HTTP|Retry-After)'
# → HTTP/1.1 429 … / Retry-After: <seconds>
```

## Scenario 6 — Governance flip (AC-08, FR-12, FR-13)

```bash
scripts/seed.sh --entries 200 --paths 1 --latency-ms 2500 | curl -s -X POST $GS/ingestion -H "X-API-Key: $GS_API_KEYS" -d @-
sleep 60
curl -s "$GS/analytics?path=/checkout&signal=latency&window=1m" -H "X-API-Key: $GS_API_KEYS" | jq ._governance
# → {"recommended_action_mode":"HITL","human_approval_required":true, …}
```

With normal seed data the same query returns `HOTL` / `false`.

## Scenario 7 — Audit trail (AC-09, FR-14)

```bash
curl -s "$GS/audit?limit=5" -H "X-API-Key: $GS_API_KEYS" | jq '.[0]'
# → {"ts":…,"endpoint":"/analytics","hashed_key":"<sha256>","trace_id":"…","status":200}
```

The raw key never appears; `hashed_key` equals `sha256(GS_API_KEYS)`.

## Scenario 8 — Full pipeline exit code (AC-10)

```bash
mvn -pl services/golden-signals verify -Dtest=PipelineIntegrationTest ; echo "exit=$?"
# → exit=0
```
