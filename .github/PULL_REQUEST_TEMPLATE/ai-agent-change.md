<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

<!-- AI/agent change (src/agents, src/guardrails, action types, autonomy). ?template=ai-agent-change.md -->

## Summary

<!-- What changed in the AI/agent surface and why. -->

## Linked issue / spec

Closes #
Spec: <!-- SPEC-NNN --> · AI safety: `docs/ai-governance/ai-safety-checklist.md`

## AI assistance

<!-- Disclose any AI involvement (CONTRIBUTING.md §5 "AI assistance", Constitution VII). Disclosure
     is provenance, not a lower bar: the same evidence and review apply. -->

- [ ] No AI tool was used for this change
- **Tool / agent:** <!-- e.g. Claude Code, GitHub Copilot, Cursor; or a delivery subagent from .claude/agents/ -->
- **Model and mode:** <!-- the model id and the mode or settings that shaped the output (plan mode, auto-accept, autonomy tier) -->
- **Extent:** <!-- what the agent drafted (code, tests, docs, PR text) and what a human wrote, rewrote or verified -->

## HITL / HOTL impact

- [ ] No change to HITL gateway / autonomy, OR change is described below
- [ ] Autonomy level / feature flags unchanged (or governance sign-off referenced: ADR-0015)

## Tool-permission changes

- [ ] New/changed tools registered in `infrastructure/agent-tools/tools.yaml` with risk/HITL/reversibility
- [ ] No permissions granted beyond `specs/ai/guardrails.md`

## Tests

- [ ] Prompt-injection tests pass (`tests/abuse_cases/ -m abuse_case`) — count not reduced
- [ ] Data-leakage / PII tests pass (`tests/security/`)
- [ ] Model-contract tests run if model version changed (`tests/model_contract/`)

## Guardrails & review

- [ ] Guardrails unmodified or strengthened (never weakened)
- [ ] AI Safety & Agent Governance checklist completed and attached
- [ ] AI Governance Lead review requested
