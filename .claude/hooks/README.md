<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Claude Code hooks

Project-wide harness hooks, wired in [`.claude/settings.json`](../settings.json) and shared
with the whole team (checked into git).

## `high-risk-action-guard.py` — PreToolUse guard (F7 / issue #133)

A `PreToolUse` hook (matches `Bash`, `Edit`, `Write`, `MultiEdit`, `NotebookEdit`) that moves
the "never autonomously push / merge / release / deploy / change a flag" guarantees from prose
into the harness layer. It closes **F7** (`docs/sdlc/deliver-dryrun-findings.md`): the `/deliver`
skill and its `phase-executor` subagent hold an unscoped `Bash` grant, so those rules were
previously enforced only by instructions.

**Decision policy** (`permissionDecision`):

| Context                                                | High-risk action      | Result                                                            |
| ------------------------------------------------------ | --------------------- | ----------------------------------------------------------------- |
| **Subagent** (`agent_type` set, e.g. `phase-executor`) | yes                   | **`deny`** — hard-blocked; autonomous runs stop at the human gate |
| **Main session**                                       | yes                   | **`ask`** — you confirm once                                      |
| any                                                    | no (safe / read-only) | defer (exit 0) — normal permission rules                          |

> An `ask` decision blocks in a subagent context anyway (a subagent can't answer the prompt), so
> the guard is safe even if `agent_type` is unavailable — the subagent simply can't proceed.

**What counts as high-risk**

- _Bash:_ `git push`, `gh pr merge`, `gh release create`, `helm upgrade|install|rollback`,
  `kubectl apply|delete|rollout`, `make deploy*`, `make rollback`, and shell writes into
  `infrastructure/feature-flags/`. Read-only variants (`git status`, `git tag -l`, `helm list`,
  `kubectl get`) are not matched.
- _Edit/Write:_ governance-controlled paths (CLAUDE.md §8 dual-approval / §14): `src/guardrails/`,
  `src/agents/hitl_gateway.py`, `src/agents/hitl_store.py`, `src/shared/feature_flags.py`,
  `infrastructure/feature-flags/`.

The guard **fails open** — any parse error returns exit 0 (defer), so it can never brick a session.

**Test it**

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push"}}' | python3 .claude/hooks/high-risk-action-guard.py
# → {"hookSpecificOutput": {... "permissionDecision": "ask" ...}}
echo '{"tool_name":"Bash","tool_input":{"command":"git push"},"agent_type":"phase-executor"}' | python3 .claude/hooks/high-risk-action-guard.py
# → {"hookSpecificOutput": {... "permissionDecision": "deny" ...}}
```

### Systems of record (ADR-0100)

An adopting repository declares its systems of record in
[`docs/governance/systems-of-record.yaml`](../../docs/governance/systems-of-record.yaml):
CRM, ERP, billing, and any other system whose data is the business record. Each entry gives a
name, an owner, how a command reaches the system (`binaries`, `targets`) and which operations are
reads (`reads`, as regular expressions). The schema is in the file, and a worked example is in
[`systems-of-record.sample.yaml`](../../docs/governance/systems-of-record.sample.yaml).

A Bash command that reaches a declared system gets the policy above (`ask` / `deny`), unless
every segment of it is a declared read or a read-only inspector (`grep`, `head`, …). Splitting
at `;`, `&&` and `|` is deliberate. In `psql -c "SELECT 1; DELETE FROM t"`, the `DELETE` segment
matches no read, so the command asks. A command that has an extra segment, such as
`cd x && psql … -c "SELECT …"`, also asks. Asking too often is the safe direction.

What this does **not** do: the hook sees command strings. A write inside a script, an SDK call or
a program the agent starts does not look like a write to it. The main control is the read-only
client in the adopter's code ([`templates/system-of-record-client-template.md`](../../templates/system-of-record-client-template.md)).

The corpus declares nothing (`systems: []`), so the guard behaves exactly as before. A malformed
declaration is ignored, because the guard fails open. `verify-high-risk-guard.py` then reports it
as a wiring failure, so the gap shows up in C5 instead of passing silently.

## `sdd-gate.py` — UserPromptSubmit gate for the code-producing `/sdd-*` commands (ADR-0092, #22)

A `UserPromptSubmit` hook that runs only when the prompt **starts** with `/sdd-plan`, `/sdd-tasks`,
`/sdd-implement` or `/sdd-taskstoissues` (mentioning a command mid-sentence does nothing). It calls
`scripts/bash/check-prerequisites.sh --json --require-spec` for the active feature and:

| Situation                                          | Result                                                                 |
| -------------------------------------------------- | ---------------------------------------------------------------------- |
| spec `draft` / `in-review` / `superseded`          | **exit 2** — prompt blocked; stderr names the spec, status and Constitution I |
| spec `approved` / `implemented`                    | exit 0 — prints a checked/unchecked table per `checklists/*.md` as context; unchecked items remain a human "proceed anyway?" |
| no active feature, missing script, malformed input | exit 0 — fails open (a one-line context note when the feature cannot be resolved) |

It never edits files and never runs git. It is the spec-kit `before_<command>` hook shape adopted
by ADR-0092; the `after_` shape (a `Stop` hook that forces the agent to continue) was refused.

**`/sdd-bugfix fix BUG-<issue>`** (ADR-0096, #132), the only bug-fix stage that edits code, is gated
on `docs/bugs/BUG-<issue>/assessment.md`:

| Situation                                                                         | Result                                   |
| --------------------------------------------------------------------------------- | ---------------------------------------- |
| assessment missing                                                                | **exit 2** — run `/sdd-bugfix assess` first |
| last filled Decision row is not `accepted` (unfilled, `rejected`)                 | **exit 2** — a person accepts the diagnosis first |
| `**Spec:**` line missing, outside `specs/`, or naming a spec not `approved`/`implemented` | **exit 2** — Constitution I              |
| accepted, and the spec is approved/implemented or the line names a `REM-NNN`      | exit 0 — a one-line confirmation as context |
| `/sdd-bugfix fix` with no `BUG-<issue>`; `assess` and `test` stages                | exit 0 — fails open / silent             |

The hook checks that the Decision row says `accepted`, not who wrote it; the PR that carries the
assessment is where the decider is reviewed.

**Only a typed command reaches the hook.** `UserPromptSubmit` sees what a person submits, not a
skill the model invokes itself through the Skill tool, so "implement the tasks" could otherwise
start `sdd-implement` with no gate. The five gated skills (`sdd-plan`, `sdd-tasks`,
`sdd-implement`, `sdd-taskstoissues`, `sdd-bugfix`) therefore carry
`disable-model-invocation: true`: they run only when typed as `/sdd-<name>` (#138). The rendered
Copilot and Cursor copies keep the key. Codex gets `agents/openai.yaml` with
`policy.allow_implicit_invocation: false`. `tests/hooks/test_sdd_gate.py` fails when a gated
command loses the flag.

**Test it**

```bash
echo '{"user_prompt":"/sdd-implement"}' | CLAUDE_PROJECT_DIR=$PWD python3 .claude/hooks/sdd-gate.py ; echo "exit=$?"
python3 tests/hooks/test_sdd_gate.py
```

**Bypass** (rare, deliberate): comment out the hook in `.claude/settings.json`, or run the command
outside Claude Code. Changes to `settings.json` hooks are re-reviewed by Claude Code on next start
for safety, so a teammate pulling this will be prompted to approve the hook before it activates.
