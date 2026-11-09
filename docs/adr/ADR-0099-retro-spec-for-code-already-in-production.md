<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0099 — A Retro-Spec for Code Already in Production

**Status:** Accepted
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — specification process; it extends `docs/sdlc/spec-persistence-model.md`
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0085](ADR-0085-unified-spec-identifier-and-status-grammar.md) (spec id and status), [ADR-0096](ADR-0096-bug-fix-path-assess-fix-test.md) (bug-fix path), [ADR-0098](ADR-0098-adoption-profiles-and-declared-not-applicable.md) (adoption profiles)

---

## Context

Article I says no code without a spec. A repository that adopts this corpus usually already has
code in production that no spec describes. A 2026-11-06 audit of an Order-to-Cash data pipeline
that adopted the corpus found that the corpus gives that code no route:

- `spec_for_defect` (`docs/process/gates/phase-gates.yaml`) covers one unspecified behaviour at a
  time: write the missing section, or take a `REM-NNN`. It does not cover a whole system that
  predates the corpus.
- `skills/sdlc/spec-lifecycle.md` covers only legacy _naming_ (path-named specs keep their
  filename and carry an `id:`), not legacy _code_.
- Writing a spec by reading the code is the obvious move, and its failure mode is known. The
  spec copies whatever the code does, bugs included, and often adds a clause that "the
  implementation prevails where the two differ". That turns the code back into the contract,
  which `docs/sdlc/spec-persistence-model.md` rules out: code is evidence, not the contract.

The audit also reported that there was no route for amending an approved spec. That one is
already covered: rules 2 and 3 of `spec-persistence-model.md` (in-place clarification, or a new
spec that supersedes) and Spec-as-PR review. This ADR does not add a second route for it.

## Decision

We will describe code already in production with a **retro-spec**: an ordinary spec, written from
the code, that settles every divergence between the code and its intended behaviour **before**
it is approved.

1. **Same grammar, one marker.** A retro-spec is a `spec` or `feature-spec` with the usual id and
   status (ADR-0085). Its frontmatter carries `origin: retro` and the commit it describes. No new
   `kind` is added.
2. **Requirements state the intended behaviour, with evidence.** Each FR and AC is written as the
   behaviour the owner wants, and cites the code, log or runbook that shows the current behaviour
   (`file:line`, Constitution IX). A behaviour inferred with no evidence is recorded as an open
   question, not as a requirement.
3. **A divergence register.** Where the code does not do what the owner wants, the spec lists the
   divergence in a `## Divergence register` table. At approval, each row gets one decision:
   - `specify`: the current behaviour is correct, and the FR states it;
   - `fix`: the code is wrong. The row cites the bug, worked through `/sdd-bugfix` (ADR-0096)
     against the approved spec;
   - `defer`: the row is kept open, with an owner and a tracking issue.

   A spec cannot move to `approved` while a row is undecided.

4. **No "code prevails" clause.** A retro-spec may not say that the implementation wins where the
   two differ. Every known difference is a row of the register. One found later is a defect
   against the approved spec (`spec_for_defect: regression`).
5. **After approval it is an ordinary spec.** `origin: retro` stays as history, and nothing else
   about the spec is special: FR/AC ids are immutable, and changes follow `spec-persistence-model.md`.
6. **Until the retro-spec is approved,** a change to that code follows `spec_for_defect` as today:
   the missing section first, or a `REM-NNN`.

Implementation, once accepted, is a separate change: a `## Divergence register` block in
`specs/SPEC-TEMPLATE.md`, `origin` in the frontmatter schema of `build_spec_registry.py`, a
retro-spec section in `skills/sdlc/spec-lifecycle.md`, and a check that a spec with
`origin: retro` has no undecided register row once it is `approved`.

## Consequences

### Positive

- Code already in production gets a spec without pretending it was written first, and without
  making the code the contract.
- Every known gap between code and intent is decided once, by a person, at approval, and is
  traceable afterwards.
- A bug found while writing the retro-spec goes through the bug-fix path already in place.

### Negative / Trade-offs

- A retro-spec of a large system can take a long time, because each divergence needs a decision.
  `defer` keeps that from blocking approval, at the cost of open rows that someone has to close.
- Writing the intended behaviour, rather than copying the code, needs the business owner. The
  agent can draft from the code but cannot decide intent.
- One more frontmatter field and one more template section.

## Alternatives Considered

- **Do nothing.** Adopters either leave production code unspecified, which breaks Article I, or
  write specs that copy the code with a "code prevails" clause, which breaks the persistence model.
- **A new spec `kind` (`retro-spec`).** Rejected: after approval it behaves exactly like a spec,
  and every reader of `kind` would need a new case for no behavioural difference.
- **Allow "code prevails" until a later review.** Rejected: it is a standing silent spec change,
  the failure `spec-persistence-model.md` names.
- **One `REM-NNN` per change, indefinitely.** Rejected: `REM-NNN` is the escape for a single
  undecided behaviour, not the long-term state of a system.

## Compliance & Risk

Constitution I (the code gets a spec) and IX (each requirement cites evidence; an inference is an
open question). No autonomy, control-matrix or data-classification change. A retro-spec of code
that processes personal data still needs the Phase 2 classification (ADR-0064 §3), as any spec does.
