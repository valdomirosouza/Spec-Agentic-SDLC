<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0075 — Resilience Fallback Policy (degrade-open vs fail-closed)

**Status:** Accepted
**Date:** 2026-06-13
**Authors:** Valdomiro Souza
**Relates to:** [ADR-0011](ADR-0011-hitl-hotl-model.md) (HITL/HOTL), [ADR-0018](ADR-0018-db-encryption-at-rest.md) (encryption at rest), [ADR-0028](ADR-0028-dora-metrics.md) (DORA / MTTR)

---

## Context

The template's headline resilience pattern is the **in-memory fallback**: every infrastructure
dependency has an in-process substitute so the app starts and serves cleanly without a full stack
(`CLAUDE.md §0.1 Infrastructure Fallback Pattern`):

- Redis down → `InMemoryHITLStore`, `InMemoryRequestStore`
- Kafka down → `InMemoryBroker`
- DB down → `InMemoryAuditStorage` — **blocked in `app_env=production`**

These fallbacks are asserted in prose and exercised by unit tests, but the **activation behaviour
under a real outage was never chaos-tested**, and there was no ADR stating _which_ fallbacks are
allowed to degrade-open versus which must fail-closed. That distinction is a correctness and
compliance boundary, not an implementation detail: silently degrading the audit log in production
would lose immutable records (SOX/ISO), while refusing to start without Redis would be a needless
availability hit.

## Decision

Every in-memory fallback is classified **degrade-open** or **fail-closed**, and each classification
is validated by a Chaos Toolkit experiment.

1. **Degrade-open (availability over the dependency):** Redis (HITL/request stores) and Kafka
   (broker) fall back to their in-memory substitutes in **any** environment. The service stays
   healthy (`/health` → 200) and continues serving; the degradation is logged and observable.
   _Validated by_ `tests/chaos/experiments/redis-fallback-activation.yaml`.
2. **Fail-closed (integrity over availability):** the **audit log** must never use
   `InMemoryAuditStorage` in `app_env=production` — a missing DB pool raises `RuntimeError` at
   startup (`src/api/rest/main.py`) rather than silently buffering audit records that would be lost
   on pod restart. _Validated by_ `tests/chaos/experiments/db-audit-fallback-blocked.yaml`.
3. **A fallback's classification may only change via a new ADR.** Promoting the audit store to
   degrade-open, or demoting Redis to fail-closed, is an architectural decision — not a config flag.
4. **Every fallback path ships a chaos experiment** asserting its classification (degrade-open →
   service survives the outage; fail-closed → service refuses to proceed). New fallbacks add one.

## Consequences

### Positive

- The resilience pattern is now _evidenced_ (the experiments exercise real outages), not merely
  asserted — closing the gap between "we have fallbacks" and "the fallbacks behave correctly".
- The degrade-open / fail-closed boundary is explicit and ADR-gated, so an availability hack can't
  silently turn the audit log lossy in production.

### Negative / Trade-offs

- Two more experiments to maintain, and a small authoring cost per new fallback. Acceptable — it is
  the price of a _tested_ resilience claim.

### Neutral

- The full experiments run against a deployed staging stack (Chaos Toolkit). PR CI validates their
  well-formedness (`adopter:tests/chaos/test_experiments_valid.py`) **and** runs a single-fault
  resilience smoke: the W2-10 wiring this ADR originally deferred was delivered, and the Chaos
  Smoke gate is **blocking**, path-filtered to the workers / HITL / retry paths.
  [`docs/governance/gate-lifecycle.md`](../governance/gate-lifecycle.md) is the source of truth for
  that status; this ADR does not restate it, because two places stating the same fact is how they
  came to disagree. From this ADR's date (2026-06-13) until the audit of 2026-09-14 the paragraph
  above said the smoke did not exist, while the gate lifecycle recorded it as blocking — an
  authority conflict of the same class as issues #48, #49 and #50, found by a reader asking whether
  self-healing was actually exercised.

## Alternatives Considered

- **Leave fallbacks untested (status quo)** — rejected: an untested resilience pattern is a claim,
  not a control; the audit fail-closed path in particular is compliance-critical.
- **Make all fallbacks degrade-open for maximum availability** — rejected: losing audit records in
  production is an integrity/compliance failure that outweighs the availability gain.

## References

- `CLAUDE.md §0.1` (Infrastructure Fallback Pattern) · `src/api/rest/main.py` (audit prod-block)
- `adopter:reports/STRENGTHENING-PLAN.md` W2-9 · `adopter:tests/chaos/experiments/`
