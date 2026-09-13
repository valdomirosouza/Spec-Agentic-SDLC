---
name: sdd-clarify
description: Detect underspecified areas of the active feature spec with a structured coverage scan, ask at most five targeted questions one at a time (with a recommended answer), and encode each answer back into spec.md and its requirements checklist. Trigger on "clarify", "ambiguities", "open questions in the spec". Usage — /sdd-clarify [focus area].
---

# /sdd-clarify — reduce ambiguity before planning

Adapted from spec-kit `/speckit.clarify`. Runs between Phase 4 (Specification) and Phase 5
(Architecture); it is the operational form of Constitution IX and of CLAUDE.md §14.1's
"contradictory requirements are resolved by humans" trigger.

## User input

```text
$ARGUMENTS
```

## Procedure

1. Run `scripts/bash/check-prerequisites.sh --json --require-spec --paths-only` → `FEATURE_SPEC`.
   Load `memory/constitution.md`.
2. **Coverage scan** of the spec — mark each category Clear / Partial / Missing:
   functional scope & out-of-scope · roles/personas · domain & data model (entities, identity,
   lifecycle, volume) · interaction & UX flow (errors, empty states) · non-functional
   (performance, scalability, reliability, **observability**, **security & privacy**,
   **compliance: LGPD/GDPR/SOX/ISO 27001**) · integrations & failure modes · edge cases ·
   constraints & trade-offs · terminology vs `docs/glossary.md` · acceptance-criteria
   testability · placeholders (`TODO`, `[NEEDS CLARIFICATION]`, vague adjectives).
3. **Question queue** (max five, ranked by impact × uncertainty). Each question must be
   answerable by a short multiple choice (2–5 options) or ≤ 5 words. Skip anything already
   answered, stylistic, or better deferred to `/sdd-plan`.
4. **Ask one at a time**: `**Question:** <full interrogative>? (FR-NN)` · one "Why it matters"
   sentence · `**Recommended:** Option X — reason` · options table · "reply with a letter, 'yes'
   to accept, or your own short answer". Never reveal queued questions. Stop at five, at
   "done", or when all critical categories are Clear.
5. **Encode after each answer** (save immediately):
   - `## Clarifications` → `### Session YYYY-MM-DD` → `- Q: … → A: …`
   - then the owning section: FR table · user story · Key Entities · Success Criteria (turn the
     adjective into a metric) · Edge Cases · §7 Governance (PII/DPIA/HITL) · §8 Golden Signals ·
     §13 Assumptions (confirm/reject) · §12 Open Questions (resolved with reference).
   - Replace the contradicted statement; leave no obsolete alternative. Remove the marker.
6. **Escalate, don't decide**: a requirement that conflicts with a binding ADR, another
   `approved` spec or a constitution article is not a question for the user's taste — record it
   in §12 Open Questions and emit `[HITL-ESCALATE]` (CLAUDE.md §14.2).
7. **Re-validate** `checklists/requirements.md`: toggle only markers whose state changed;
   report before → after counts, newly passing, regressions, still unchecked.

## Completion report

Questions asked/answered · sections touched · checklist before/after · coverage table
(Resolved / Deferred / Clear / Outstanding) · escalations raised · next command (`/sdd-plan`
after approval, or `/sdd-clarify` again).

## Done when

- [ ] ≤ 5 questions, each encoded in spec.md with no dangling marker
- [ ] Conflicts with ADRs/specs escalated, not resolved unilaterally
- [ ] requirements.md re-evaluated and reported
