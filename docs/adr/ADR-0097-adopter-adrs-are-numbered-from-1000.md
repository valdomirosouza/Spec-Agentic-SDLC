<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0097 — Adopter ADRs Are Numbered From 1000

**Status:** Accepted
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — numbering policy for the corpus and the repositories that adopt it
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0059](ADR-0059-reusability-uplift.md) (ADRs are append-only and immutable), [ADR-0091](ADR-0091-corpus-adoption-script-and-per-agent-skill-copies.md) (adoption script), [ADR-0096](ADR-0096-bug-fix-path-assess-fix-test.md) (the number that collided)

---

## Context

The `governed` and `full` adoption layers copy `docs/adr/` into the adopting repository
(`scripts/bash/adopt.sh`, `SETUP.md`). The adopter then writes its own ADRs in the same directory.
No rule says which numbers belong to whom. An adopter that takes the next free number collides
with this corpus as soon as the corpus adds an ADR with that number.

That has happened. A 2026-11-06 audit of a repository that adopted the corpus to run a monthly
Order-to-Cash data pipeline found a local ADR-0096 beside this corpus's
[ADR-0096](ADR-0096-bug-fix-path-assess-fix-test.md). Two forces make the collision hard to undo:

- **ADRs are immutable** ([ADR-0059](ADR-0059-reusability-uplift.md), `docs/adr/README.md`).
  Neither side may renumber, move or rename an ADR file to make room.
- **`check-corpus.sh` C3 requires numbering contiguous from 0001** and fails on a duplicate
  number. An adopter with a collision, or with its own numbers past a gap, fails C3 permanently.

## Decision

We will reserve **ADR-0001 to ADR-0999 for this corpus** and number **every adopter ADR from
ADR-1000 upward**.

1. **Two ranges, each contiguous.** The corpus range runs from ADR-0001. The adopter range runs
   from ADR-1000. C3 checks each range for gaps on its own, so a new corpus ADR never breaks an
   adopter, and an adopter ADR never breaks a corpus sync.
2. **The adopter indexes its range separately.** `docs/adr/README.md` in the adopting repository
   gains a "Local ADRs (1000+)" table. The corpus index stays as shipped, so a sync replaces it
   without merging.
3. **Existing collisions are restated, never renamed.** An adopter ADR in the corpus range is
   re-recorded as a new ADR in the 1000+ range, with the same decision. The old file is kept and
   its status becomes `Superseded by ADR-1NNN`, in place, as ADR-0059 requires. C3 accepts a
   duplicate number in the corpus range only when one of the two files is `Superseded by` an
   ADR numbered 1000 or above.
4. **References follow the restatement.** New text cites the 1000+ number. Old text keeps the old
   citation, which still resolves to the superseded file and from there to its successor.

Implementation, once accepted, is a separate change: C3 in `scripts/bash/check-corpus.sh` and its
tests, the index section and a note in `SETUP.md` and `docs/adr/README.md`.

## Consequences

### Positive

- A corpus sync can never collide with an adopter ADR again.
- The fix for an existing collision keeps every file and every citation, so the audit trail is
  intact (Constitution VII).
- An ADR number tells a reader where the decision came from: below 1000 is the corpus, from 1000
  up is the adopting repository.

### Negative / Trade-offs

- The corpus is limited to 999 ADRs. At the current rate (96 since the template's start) this is
  not a near-term limit.
- An adopter with collisions does one restatement per colliding ADR, and its C3 accepts a
  superseded duplicate, which is a special case in the check.
- An adopter's first local ADR is ADR-1000, not the next number after the corpus. A reader who
  expects one sequence has to learn the two ranges.

## Alternatives Considered

- **Do nothing.** Every future corpus ADR can collide with an adopter, and C3 fails permanently
  for any adopter that has a collision.
- **A prefix for adopter ADRs** (`LADR-0001`, `<ORG>-ADR-0001`). Rejected: every tool that reads
  `ADR-NNNN`, from C3 to the index links and the `Refs:` grammar (CLAUDE.md §6), would need a
  second pattern. A number range keeps one grammar.
- **A separate directory** (`docs/adr/local/`). Rejected for the same reason: every reader of
  `docs/adr/` would need to know about it, and the numbers could still collide in citations.
- **Renumber the colliding adopter ADRs.** Rejected: it breaks ADR-0059, and every citation of
  the old number would silently point at the corpus ADR that took it.

## Compliance & Risk

No autonomy impact (ADR-0015), no control-matrix change and no data-classification change. The
decision protects Constitution VII: no ADR file is renamed, moved or deleted.
