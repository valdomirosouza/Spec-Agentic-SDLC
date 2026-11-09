<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# ADR-0100 — Systems of Record Are Read-Only to Dev-Time Agents

**Status:** Accepted
**Date:** 2026-11-09
**Authors:** Tech Lead (drafted with Claude Code)
**Spec:** N/A — dev-time agent governance
**Supersedes:** None | **Superseded by:** None
**Relates to:** [ADR-0034](ADR-0034-agentic-escalation-protocol.md) (escalation), [ADR-0092](ADR-0092-command-lifecycle-hooks-vs-claude-code-hooks.md) (Claude Code hooks), [ADR-0011](ADR-0011-hitl-hotl-model.md) (HITL/HOTL), [ADR-0098](ADR-0098-adoption-profiles-and-declared-not-applicable.md) (adoption profiles)

---

## Context

`.claude/hooks/high-risk-action-guard.py` is a PreToolUse hook. It asks in the main session, and
denies in a subagent, before an outward-facing or irreversible action:

- a push, PR merge, release, deploy or rollback, or a write into the feature-flag directory;
- an edit to the guardrails, the HITL gateway or the feature-flag config.

The guard knows this repository's own risks. It knows nothing about the adopter's.

A 2026-11-06 audit of an Order-to-Cash data pipeline that adopted the corpus found that its
dev-time agents run shell and SQL against the company's **systems of record** (CRM, ERP): the
systems whose data is the authoritative business record. Nothing in the corpus distinguished a
read from a write against them. The adopter built its own read-only guard.

A write to a system of record from a development session is the outward-facing, hard-to-reverse
action the guard exists for. It is also the one the guard cannot see, because the systems are the
adopter's and differ in every repository.

## Decision

We will treat **every write to a declared system of record as a high-risk action**. Reads stay
free. Three layers enforce it, each catching what the others miss.

1. **Declared, not guessed.** The adopter lists its systems of record in
   `docs/governance/systems-of-record.yaml`. Each entry gives:
   - a name and an owner;
   - how it is reached: CLI binaries, connection or profile names, host or URL patterns;
   - the operations that are reads.

   An empty or absent file means "none declared", and nothing changes.

2. **The guard asks before a write.** `high-risk-action-guard.py` reads the declaration. A Bash
   command that reaches a declared system with an operation not listed as a read gets the guard's
   existing policy: `ask` in the main session, `deny` in a subagent. A read passes.
3. **A code-level client is the main control.** Production and script code reaches each system of
   record through one client that is read-only by default. A write needs an explicit write
   client, constructed in one reviewed place. That client is adopter code (adopter-provided).
   The corpus states the contract and a test template.
4. **A test keeps the layers honest.** The guard's suite gains cases built from a sample
   declaration: a write is asked or denied, a read passes, and a malformed file fails open. The
   adopter's CI runs the test template against its own client.

Implementation, once accepted, is a separate change:

- the declaration schema and a sample;
- the guard's reader and its test cases;
- the client contract and test template, under the adopter-paths marker;
- a section in `.claude/hooks/README.md`.

## Consequences

### Positive

- The most damaging dev-time mistake in a data repository, writing to the business record, gets
  the same human gate as a push or a deploy.
- The adopter declares its systems once, in a file a reviewer reads. The corpus never hard-codes
  anyone's CRM or ERP.
- The guard's default (nothing declared) is today's behaviour.

### Negative / Trade-offs

- **The hook only sees command strings.** A write hidden inside a script, an SDK call, or a
  connection opened by a program the agent runs does not look like a write to the hook. That is
  why the code-level client is the main control and the hook is defence in depth. The ADR does
  not claim the hook alone makes a system read-only.
- **The guard fails open on any error**, as it does today. A malformed declaration therefore
  disables the new check, and the test case for that makes the failure visible rather than silent.
- Declaring the operations that count as reads takes work, and a missing read makes the guard ask
  more often than needed. Asking too often is the safe direction.

## Alternatives Considered

- **Do nothing.** Each adopter builds its own guard, or does not, and a write to a system of record
  from a development session stays ungated.
- **Deny every command that reaches a system of record, read or write.** Rejected: data work needs
  reads, and a guard that blocks reads gets switched off.
- **Rely on database permissions alone** (a read-only account for development). Kept as good
  practice, but not as the decision: the corpus cannot provision credentials. A shared or
  over-privileged account is common, and permissions do not cover CLIs and APIs.
- **A per-adopter fork of the guard.** Rejected: forks drift from the corpus, and the guard's own
  fixes stop reaching them.

## Compliance & Risk

Constitution V (human oversight of agent actions): a write to the business record is a
consequential action and gets a human gate. No autonomy-flag change (ADR-0015). The hook is
strengthened and never weakened, and its fail-open behaviour is unchanged and documented. No
control-matrix or data-classification change. A declaration names systems and patterns and
never holds credentials, so no secret enters the file (CLAUDE.md §3.2).
