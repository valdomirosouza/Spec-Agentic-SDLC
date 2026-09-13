# Roadmap: [EPIC NAME]

<!--
  "Spec of specs" (adopted from spec-kit docs/concepts/spec-of-specs.md). Use ONLY when an epic is
  too large for one specify → plan → tasks → implement cycle even after scoping runs per phase.
  The roadmap names and orders slices; it does not design them — each slice gets its own spec.
  Keep IDs immutable once a sub-spec references them; they are the traceability anchor.
-->

[One or two sentences: what the epic is and why it is decomposed.]

**Owner**: [Product Owner] | **Risk class**: [normal / high / ai / security / infra]
**Status legend**: planned · in-progress · done · superseded

| ID  | Sub-feature | Intent (one line) | Scope boundary (in / deferred) | Depends on | Status  | Sub-spec (`specs/features/…`) |
| --- | ----------- | ----------------- | ------------------------------ | ---------- | ------- | ----------------------------- |
| R1  |             |                   |                                | —          | planned | —                             |
| R2  |             |                   |                                | R1         | planned | —                             |

## Conventions

- Each sub-spec's frontmatter sets `roadmap: <this file> → R<n>`; the row above links back to
  the sub-spec directory. Both directions are plain text and greppable.
- Update the roadmap first when scope shifts, then reconcile the affected sub-specs.
- Independent slices may run in parallel in separate worktrees; dependent slices wait for `done`.
- A slice that is still too large gets its own roadmap one level down.
