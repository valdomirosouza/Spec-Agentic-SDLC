<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0098 — Adoption Profiles and a Declared "Not Applicable"

**Status:** Accepted
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — adoption and governance policy
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0064](ADR-0064-delivery-right-sizing-tiers.md) (tiers and the control floor), [ADR-0061](ADR-0061-control-binding-ci-gate.md) (applicability matrix), [ADR-0070](ADR-0070-governance-gate-enforcement-lifecycle.md) (gate lifecycle), [ADR-0091](ADR-0091-corpus-adoption-script-and-per-agent-skill-copies.md) (adoption script), [ADR-0097](ADR-0097-adopter-adrs-are-numbered-from-1000.md)

---

## Context

The corpus assumes that an adopter ships a deployed service: probes, canary, a request path,
Golden Signals of a live endpoint. A 2026-11-06 audit of a repository that adopted it to run a
monthly Order-to-Cash data pipeline (shell and SQL extractions, stdlib Python, manual runs) found
that this assumption has no exit:

- **11 `check-corpus.sh` checks failed permanently** in the adopter, because they test for things
  a batch pipeline does not have. A permanently red run hides new failures: a broken-link
  regression from 9 to 315 links went unnoticed among them.
- There is **no way to declare that a check does not apply**. The only escape is to stop running
  the check, which is silent.

The corpus already has the pieces of an answer, but not the answer:

- **Tiers** ([ADR-0064](ADR-0064-delivery-right-sizing-tiers.md)) right-size the _process_ of one
  delivery. A `conditional` phase is recorded `N/A` when its condition (for example
  `deploys_prod`) does not hold. Tiers describe a change, not the shape of the repository.
- **`applicability-matrix.yml`** declares regulatory scope with `in_scope` and a `rationale`
  (ADR-0061), for SOX, ISO 27001 and the privacy jurisdictions. It does not cover checks.
- **`check-corpus.sh`** skips the checks that audit the corpus governing itself when it runs in an
  adopter (`CORPUS_ONLY`), and C3 prints `n/a` when there is no ADR index. Both are decided by the
  corpus, not declared by the adopter.

## Decision

We will add an **adoption profile** beside the tiers, and a **declared `n/a`** that replaces a
permanent failure with a recorded, reviewable decision.

1. **Profiles describe the repository; tiers describe the change.** An adopter declares one
   profile in `docs/governance/applicability-matrix.yml`:
   - `service` (the default, today's behaviour): a deployed service with a request path;
   - `batch-data`: scheduled or manual runs over data, with no long-running endpoint.

   A profile sets the defaults of the existing `applicability_conditions` in
   `phase-gates.yaml`. For example, `batch-data` has no `deploys_prod` canary. It never changes
   the tiers or which phases are control phases. What a batch run owes instead (run records, data
   evidence, reconciliation) is decided in separate ADRs.

2. **`n/a` is declared, never inferred.** The same file gains a `not_applicable:` list. Each entry
   names a check exactly as `check-corpus.sh` prints it, a `reason`, an `owner` and a `review_by`
   date. `check-corpus.sh` then prints that check as `n/a: <reason>`. It is not counted as a
   failure, and it is not hidden: the run lists every declared `n/a`.
3. **The control floor cannot be declared `n/a`.** A check that enforces a protected
   Constitution article (I, II, V, VII, IX), or a control phase of ADR-0064 §3, is refused.
   Declaring it fails the run. Examples are the high-risk-action guard (`verify-high-risk-guard`,
   Article V) and the sdd-gate suite (`tests/hooks/test_sdd_gate.py`, Article I). The
   implementation names the full refused list in one place, in the script, with a test.
4. **A declaration expires.** After `review_by`, the check runs again and fails if it fails. This
   keeps an `n/a` from becoming the permanent state it replaced (the ADR-0070 lifecycle, applied to
   a declaration rather than a gate).

Implementation, once accepted, is a separate change: the `applicability-matrix.yml` schema, the
`check-corpus.sh` reader with its refused list and tests, the profile defaults in
`phase-gates.yaml`, and a `SETUP.md` section.

## Consequences

### Positive

- An adopter whose shape differs from a service gets a green run that means something, so a new
  failure is visible again.
- Every exemption has a reason, an owner and an end date, in a file a reviewer reads.
- The protected articles and the ADR-0064 control floor stay where they are, for every profile.

### Negative / Trade-offs

- A second axis beside the tiers. Readers have to tell "which phases this change needs" (tier)
  from "which checks this repository can run" (profile).
- The refused list has to be kept current: a new check that enforces a protected article must be
  added to it, or it could be declared `n/a`.
- An `n/a` only expires on its date. An adopter can renew it with a new date, and the renewal is
  as visible as the first declaration, but it is not blocked.

## Alternatives Considered

- **Do nothing.** Adopters keep permanently red runs, or stop running the checks, and either way
  a regression goes unseen.
- **Per-check flags on the command line** (`check-corpus.sh --skip <check>`). Rejected: a flag
  leaves no record and no reason, and lives in whatever runs the command.
- **More tiers** (a `BATCH` tier). Rejected: tiers size one delivery. Making them describe the
  repository mixes two questions and would weaken the rule that tiers trim process, never
  controls.
- **Let the corpus detect the shape** (no `services/`, so a batch profile). Rejected: inferred
  exemptions are silent, and the audit's point is that exemptions must be declared.

## Compliance & Risk

No autonomy impact (ADR-0015). No control-matrix or data-classification change. The decision
narrows a risk: today an adopter can only silence a check by not running it. The refused list
keeps the protected Constitution articles outside the mechanism.
