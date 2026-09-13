<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Spec registry

> **Generated** by `scripts/python/build_spec_registry.py --build` from the ADR-0085
> frontmatter of every spec on disk. Do not edit by hand. `check-corpus.sh` C13 fails when
> this file or its JSON companion disagrees with disk, which is what let the registry drift
> to 50 of 58 entries before issue #47.

**58 specs** · approved: 50 · draft: 4 · implemented: 3 · superseded: 1

| Spec | Kind | Status | Owner | Issue | Path | Governing ADRs | Impl | Verif |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SPEC-AI-001 | spec | approved | AI Lead |  | `specs/ai/agent-design.md` | ADR-0010, ADR-0011, ADR-0012 | 5 (5 unmarked) | 3 (3 unmarked) |
| SPEC-AI-002 | spec | approved | unassigned |  | `specs/ai/agent-memory.md` | ADR-0017 | 5 (5 unmarked) | 4 (4 unmarked) |
| SPEC-AI-003 | spec | approved | AI Governance Lead |  | `specs/ai/agentic-maturity-assessment.md` | ADR-0040 | 1 | 0 |
| SPEC-AI-004 | spec | approved | unassigned |  | `specs/ai/autonomous-mode-levels.md` | ADR-0015 | 2 (2 unmarked) | 0 |
| SPEC-AI-005 | spec | approved | AI Governance Lead |  | `specs/ai/context-graph.md` | ADR-0041 | 2 (2 unmarked) | 0 |
| SPEC-AI-006 | spec | approved | unassigned |  | `specs/ai/feedback-loop.md` | — | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-AI-007 | spec | approved | Security Lead |  | `specs/ai/guardrails.md` | ADR-0011, ADR-0012 | 5 (5 unmarked) | 10 (10 unmarked) |
| SPEC-AI-008 | spec | approved | AI Lead |  | `specs/ai/harness-design.md` | ADR-0010, ADR-0011, ADR-0014 | 7 (7 unmarked) | 7 (7 unmarked) |
| SPEC-AI-009 | spec | approved | AI Lead |  | `specs/ai/hitl-hotl.md` | ADR-0011 | 11 (11 unmarked) | 7 (7 unmarked) |
| SPEC-AI-010 | spec | draft | ai-governance-lead |  | `specs/ai/rag-pipeline.md` | ADR-0017, ADR-0018, ADR-0019, ADR-0038, ADR-0080 | 0 | 0 |
| SPEC-AI-011 | spec | approved | AI Lead + Security Lead |  | `specs/ai/hitl-notification.md` | ADR-0003, ADR-0011 | 1 (1 unmarked) | 0 |
| SPEC-AI-012 | spec | approved | AI Governance Lead |  | `specs/ai/learn-stage.md` | ADR-0038 | 1 (1 unmarked) | 0 |
| SPEC-AI-013 | spec | approved | Tech Lead |  | `specs/ai/long-running-session.md` | ADR-0014, ADR-0033 | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-AI-014 | spec | approved | unassigned |  | `specs/ai/sandbox-execution.md` | ADR-0016 | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-AI-015 | spec | approved | Tech Lead |  | `specs/ai/sub-agent-specialization.md` | ADR-0014, ADR-0032 | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-AI-016 | spec | approved | Security Lead |  | `specs/ai/tool-registry.md` | ADR-0039 | 1 (1 unmarked) | 0 |
| SPEC-AI-020 | policy | approved | Security Lead | 41 | `specs/ai/red-team-program.md` | ADR-0050, ADR-0036, ADR-0048, ADR-0093 | 0 | 0 |
| SPEC-API-001 | spec | approved | valdomirosouza |  | `specs/api/SPEC-API-001-error-model-and-request-correlation.md` | ADR-0004, ADR-0012, ADR-0024, ADR-0026, ADR-0029 | 3 (3 unmarked) | 1 (1 unmarked) |
| SPEC-API-002 | spec | implemented | valdomirosouza |  | `specs/api/SPEC-API-002-idempotency-keys.md` | ADR-0009, ADR-0019, ADR-0024, ADR-0076 | 1 | 1 |
| SPEC-API-003 | spec | implemented | valdomirosouza |  | `specs/api/SPEC-API-003-pagination.md` | ADR-0024, ADR-0076 | 2 | 0 |
| SPEC-API-004 | spec | draft | valdomirosouza |  | `specs/api/SPEC-API-004-runs-trace-and-slo-status.md` | ADR-0076, ADR-0011, ADR-0004 | 2 (2 unmarked) | 2 (2 unmarked) |
| SPEC-API-005 | spec | approved | Tech Lead |  | `specs/api/async-api-design.md` | ADR-0003, ADR-0005, ADR-0012 | 3 (2 unmarked) | 1 (1 unmarked) |
| SPEC-COMP-001 | spec | approved | Tech Lead, DevOps Lead |  | `specs/compliance/iso27001-change-management.md` | ADR-0027 | 2 (2 unmarked) | 0 |
| SPEC-COMP-002 | spec | approved | Tech Lead, Security Lead |  | `specs/compliance/sox-controls.md` | ADR-0026 | 1 (1 unmarked) | 0 |
| SPEC-COMP-010 | policy | approved | AI Governance Lead | 27 | `specs/compliance/ai-post-market-monitoring.md` | ADR-0093, ADR-0011, ADR-0049, ADR-0051, ADR-0080 | 0 | 0 |
| SPEC-DATA-001 | spec | approved | Tech Lead | 29 | `specs/data/data-quality.md` | ADR-0003, ADR-0012, ADR-0013 | 0 | 0 |
| SPEC-DATA-002 | spec | approved | Tech Lead | 30 | `specs/data/data-contracts.md` | ADR-0003, ADR-0024, ADR-0047 | 0 | 0 |
| SPEC-DATA-003 | spec | approved | Tech Lead | 32 | `specs/data/data-lineage.md` | ADR-0012, ADR-0013, ADR-0043, ADR-0044 | 0 | 0 |
| SPEC-ETH-001 | policy | approved | AI Governance Lead |  | `specs/ethics/ethical-ai-principles.md` | ADR-0011, ADR-0015, ADR-0016 | 0 | 0 |
| SPEC-FEAT-001 | feature-spec | implemented | Tech Lead | 357 | `specs/features/SPEC-FEAT-001-http-golden-signals/spec.md` | ADR-0006, ADR-0043, ADR-0089 | 2 | 2 |
| SPEC-GOV-001 | policy | approved | unassigned |  | `specs/governance/team-topology.md` | — | 0 | 0 |
| SPEC-INFRA-001 | spec | approved | valdomirosouza |  | `specs/infrastructure/SPEC-INFRA-001-aws-platform-terraform.md` | — | 1 (1 unmarked) | 0 |
| SPEC-K8S-001 | spec | approved | unassigned |  | `specs/k8s/probe-strategy.md` | ADR-0042 | 2 (2 unmarked) | 0 |
| SPEC-LGS-001 | feature-spec | superseded | valdomirosouza |  | `specs/features/SPEC-LGS-001-golden-signals-feature-spec.md` | ADR-0003, ADR-0011, ADR-0012, ADR-0020, ADR-0026, ADR-0066, ADR-0067 | 0 | 0 |
| SPEC-LGS-001 | feature-spec | approved | valdomirosouza |  | `specs/features/SPEC-LGS-001-log-based-golden-signals/spec.md` | ADR-0003, ADR-0011, ADR-0012, ADR-0020, ADR-0025, ADR-0026, ADR-0029, ADR-0066, ADR-0067, ADR-0068, ADR-0069 | 0 | 0 |
| SPEC-LGS-001 | threat-model | draft | Security Lead |  | `specs/security/threat-model-SPEC-LGS-001-golden-signals.md` | ADR-0011, ADR-0012, ADR-0019, ADR-0020, ADR-0026, ADR-0066, ADR-0067, ADR-0068, ADR-0069 | 0 | 0 |
| SPEC-LGS-001 | spec | draft | valdomirosouza |  | `specs/system/SPEC-LGS-001-log-based-golden-signals.md` | — | 0 | 0 |
| SPEC-OBS-001 | spec | approved | SRE Lead |  | `specs/observability/agent-performance.md` | ADR-0004 | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-OBS-002 | spec | approved | unassigned |  | `specs/observability/agent-supervision.md` | — | 1 (1 unmarked) | 0 |
| SPEC-OBS-003 | spec | approved | SRE Lead |  | `specs/observability/dora-metrics.md` | ADR-0028 | 2 (2 unmarked) | 0 |
| SPEC-OBS-004 | spec | approved | unassigned |  | `specs/observability/otel-agentic-observability.md` | ADR-0043, ADR-0044, ADR-0045, ADR-0046 | 2 (2 unmarked) | 1 (1 unmarked) |
| SPEC-PRIV-001 | spec | approved | DPO |  | `specs/privacy/data-retention.md` | ADR-0012, ADR-0013 | 1 (1 unmarked) | 0 |
| SPEC-PRIV-002 | spec | approved | unassigned |  | `specs/privacy/db-encryption-at-rest.md` | ADR-0018 | 1 (1 unmarked) | 1 (1 unmarked) |
| SPEC-PRIV-003 | policy | approved | DPO |  | `specs/privacy/dpia-ripd.md` | ADR-0012, ADR-0013 | 0 | 0 |
| SPEC-PRIV-004 | spec | approved | DPO |  | `specs/privacy/pii-inventory.md` | ADR-0012, ADR-0013 | 1 (1 unmarked) | 0 |
| SPEC-PRIV-005 | spec | approved | unassigned |  | `specs/privacy/redis-tls.md` | ADR-0019 | 2 (2 unmarked) | 1 (1 unmarked) |
| SPEC-PRIV-010 | policy | approved | DPO | 34 | `specs/privacy/training-data-governance.md` | ADR-0012, ADR-0013, ADR-0093 | 0 | 0 |
| SPEC-PRIV-011 | spec | approved | DPO | 35 | `specs/privacy/test-data-management.md` | ADR-0012, ADR-0013, ADR-0018 | 0 | 0 |
| SPEC-SDLC-001 | policy | approved | Tech Lead |  | `specs/sdlc/development-lifecycle.md` | ADR-0001, ADR-0003, ADR-0006 | 0 | 0 |
| SPEC-SEC-001 | policy | approved | Security Lead |  | `specs/security/pentest-checklist.md` | — | 0 | 0 |
| SPEC-SEC-002 | spec | approved | Security Lead |  | `specs/security/rbac-model.md` | ADR-0008, ADR-0011, ADR-0023 | 1 (1 unmarked) | 0 |
| SPEC-SEC-003 | policy | approved | Security Lead |  | `specs/security/threat-model.md` | ADR-0008, ADR-0011, ADR-0012, ADR-0016, ADR-0018, ADR-0019 | 0 | 1 (1 unmarked) |
| SPEC-SRE-001 | policy | approved | unassigned |  | `specs/sre/capacity-planning.md` | — | 0 | 0 |
| SPEC-SRE-002 | policy | approved | unassigned |  | `specs/sre/finops.md` | ADR-0020 | 0 | 0 |
| SPEC-SYS-001 | spec | approved | Tech Lead |  | `specs/system/architecture.md` | ADR-0011 | 7 (7 unmarked) | 5 (5 unmarked) |
| SPEC-SYS-002 | spec | approved | Tech Lead |  | `specs/system/async-event-flow.md` | ADR-0003, ADR-0005 | 2 (2 unmarked) | 0 |
| SPEC-SYS-003 | spec | approved | Tech Lead |  | `specs/system/request-pipeline.md` | ADR-0003, ADR-0005, ADR-0009, ADR-0011, ADR-0012 | 4 (4 unmarked) | 5 (5 unmarked) |
| SPEC-SYS-004 | policy | approved | Product Owner |  | `specs/system/vision.md` | — | 0 | 0 |

## By kind

| Kind | Count |
| --- | --- |
| feature-spec | 3 |
| policy | 12 |
| spec | 42 |
| threat-model | 1 |

## Evidence accounting

An evidence path is accounted for when it resolves on disk or carries an explicit
`adopter:` / `ci:` / `planned:` marker. Directory shape is not an exemption: exempting
anything under `src/`, `tests/` or `.github/workflows/` left 145 of 146 paths unchecked
and the rule could no longer catch the case it was written for (R5-T4).

- **Unresolved — resolves nowhere, marked nowhere:** 0. This is the finding.
- **Unmarked — shaped like an adopter path, missing its marker:** 136 across 34 specs. Minor: the fix is one prefix per line.

### Marking backlog

| Spec | Paths to mark |
| --- | --- |
| SPEC-AI-001 | 8 |
| SPEC-AI-002 | 9 |
| SPEC-AI-004 | 2 |
| SPEC-AI-005 | 2 |
| SPEC-AI-006 | 2 |
| SPEC-AI-007 | 15 |
| SPEC-AI-008 | 14 |
| SPEC-AI-009 | 18 |
| SPEC-AI-011 | 1 |
| SPEC-AI-012 | 1 |
| SPEC-AI-013 | 2 |
| SPEC-AI-014 | 2 |
| SPEC-AI-015 | 2 |
| SPEC-AI-016 | 1 |
| SPEC-API-001 | 4 |
| SPEC-API-004 | 4 |
| SPEC-API-005 | 3 |
| SPEC-COMP-001 | 2 |
| SPEC-COMP-002 | 1 |
| SPEC-INFRA-001 | 1 |
| SPEC-K8S-001 | 2 |
| SPEC-OBS-001 | 2 |
| SPEC-OBS-002 | 1 |
| SPEC-OBS-003 | 2 |
| SPEC-OBS-004 | 3 |
| SPEC-PRIV-001 | 1 |
| SPEC-PRIV-002 | 2 |
| SPEC-PRIV-004 | 1 |
| SPEC-PRIV-005 | 3 |
| SPEC-SEC-002 | 1 |
| SPEC-SEC-003 | 1 |
| SPEC-SYS-001 | 12 |
| SPEC-SYS-002 | 2 |
| SPEC-SYS-003 | 9 |
