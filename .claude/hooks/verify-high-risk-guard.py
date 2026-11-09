#!/usr/bin/env python3
"""Verify the F7 high-risk-action guard (issue #133) — run via `make verify-f7-hook`.

This checks the guard's **decision logic** and its **wiring** in settings.json:
  * feeds the real hook representative PreToolUse payloads and asserts the
    permissionDecision (deny for subagents / ask in the main session / defer for
    safe & read-only), including the bypass variants an adversarial review found;
  * confirms `.claude/settings.json` registers the hook on the right tools.

It does NOT (and cannot) verify runtime *activation* — whether a live Claude Code
session has loaded the hook. That requires restarting Claude Code and approving
the hook; confirm it there with `git push --dry-run` (→ ask) once restarted.

Exit 0 = all checks pass; exit 1 = a failure (use as a regression gate).
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
GUARD = _HERE / "high-risk-action-guard.py"
SETTINGS = _HERE.parent / "settings.json"
SOR_DECLARATION = _HERE.parents[1] / "docs" / "governance" / "systems-of-record.yaml"
SOR_SAMPLE = SOR_DECLARATION.with_name("systems-of-record.sample.yaml")


def _decide(payload: object, guard: Path = GUARD) -> str:
    """Run the guard with `payload` on stdin; return ask|deny|defer|ERROR:<…>."""
    proc = subprocess.run(  # noqa: S603 — fixed argv (this interpreter + a trusted in-repo script), self-authored test JSON on stdin
        [sys.executable, str(guard)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return f"ERROR:exit{proc.returncode}"
    out = proc.stdout.strip()
    if not out:
        return "defer"
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]
    except Exception:
        return f"ERROR:badoutput({out[:40]!r})"


def _bash(command: object, agent: str | None = None) -> dict:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    if agent:
        payload["agent_type"] = agent
    return payload


def _edit(path: object, agent: str | None = None, tool: str = "Edit") -> dict:
    payload = {"tool_name": tool, "tool_input": {"file_path": path}}
    if agent:
        payload["agent_type"] = agent
    return payload


# (description, payload, expected-decision)
CASES: list[tuple[str, object, str]] = [
    # --- high-risk in the main session -> ASK (incl. review-found bypasses) ---
    ("main · git push", _bash("git push origin main"), "ask"),
    ("main · git -C dir push (bypass)", _bash("git -C /repo push"), "ask"),
    ("main · git --git-dir=x push (bypass)", _bash("git --git-dir=/r/.git push"), "ask"),
    ("main · /usr/bin/git push (bypass)", _bash("/usr/bin/git push"), "ask"),
    ("main · $(git push) (bypass)", _bash("x=$(git push)"), "ask"),
    ("main · eval 'git push' (bypass)", _bash("eval 'git push'"), "ask"),
    ("main · gh pr merge", _bash("gh pr merge 5 --squash"), "ask"),
    ("main · gh pr create", _bash("gh pr create --title x --body y"), "ask"),
    ("main · gh pr ready", _bash("gh pr ready 7"), "ask"),
    ("main · gh release create", _bash("gh release create v1"), "ask"),
    # W14-T6: the vcs.sh shim must not bypass the guard.
    ("main · scripts/vcs.sh pr merge", _bash("scripts/vcs.sh pr merge 5 --squash"), "ask"),
    ("main · vcs.sh pr create", _bash("bash scripts/vcs.sh pr create --title x"), "ask"),
    ("main · vcs.sh release create", _bash("./scripts/vcs.sh release create v1"), "ask"),
    ("main · vcs.sh issue list (safe)", _bash("scripts/vcs.sh issue list --state open"), "defer"),
    # real action after a read-only segment must still flag
    ("main · cat x && git push", _bash("cat notes && git push"), "ask"),
    ("main · echo $(git push) (cmd subst executes)", _bash("echo $(git push)"), "ask"),
    ("main · helm upgrade", _bash("helm upgrade app ./chart"), "ask"),
    ("main · kubectl apply", _bash("kubectl apply -f x.yaml"), "ask"),
    ("main · make deploy-staging", _bash("make deploy-staging SERVICE=x"), "ask"),
    ("main · make rollback", _bash("make rollback"), "ask"),
    (
        "main · write feature-flags",
        _edit("infrastructure/feature-flags/f.json", tool="Write"),
        "ask",
    ),
    ("main · edit guardrails", _edit("src/guardrails/pii_filter.py"), "ask"),
    # --- safe / read-only -> DEFER (no false positives) ---
    ("main · git status", _bash("git status"), "defer"),
    ("main · git tag -l", _bash("git tag -l"), "defer"),
    ("main · git log --grep=push", _bash("git log --grep=push"), "defer"),
    ('main · git commit -m "…push…"', _bash('git commit -m "fix push bug"'), "defer"),
    # read-only inspection of a high-risk literal must NOT flag (the bug this fixes)
    ("main · grep 'git push' (read-only)", _bash("grep -n 'git push' .claude/hooks/x.py"), "defer"),
    ("main · echo 'git push' (read-only)", _bash("echo 'git push'"), "defer"),
    ("main · rg 'gh pr create' (read-only)", _bash("rg 'gh pr create' docs/"), "defer"),
    ("main · cat x | grep 'make deploy'", _bash("cat ci.yml | grep 'make deploy'"), "defer"),
    ("main · helm list", _bash("helm list"), "defer"),
    ("main · make test-unit-python", _bash("make test-unit-python"), "defer"),
    ("main · make deployment-check (FP guard)", _bash("make deployment-check"), "defer"),
    ("main · edit README", _edit("README.md"), "defer"),
    # --- subagent context -> DENY (autonomous runs hard-blocked) ---
    ("subagent · git -C . push", _bash("git -C . push", agent="phase-executor"), "deny"),
    ("subagent · gh pr create", _bash("gh pr create -t x", agent="phase-executor"), "deny"),
    ("subagent · vcs.sh pr merge", _bash("scripts/vcs.sh pr merge 5", agent="phase-executor"), "deny"),
    ("subagent · make deploy", _bash("make deploy-staging", agent="phase-executor"), "deny"),
    ("subagent · edit guardrails", _edit("src/guardrails/x.py", agent="phase-executor"), "deny"),
    ("subagent · make lint (safe)", _bash("make lint-python", agent="phase-executor"), "defer"),
    # --- malformed input -> fail OPEN (defer, never crash) ---
    (
        "fail-open · command=123 (int)",
        {"tool_name": "Bash", "tool_input": {"command": 123}},
        "defer",
    ),
    (
        "fail-open · file_path=99 (int)",
        {"tool_name": "Edit", "tool_input": {"file_path": 99}},
        "defer",
    ),
    ("fail-open · payload is a list", [], "defer"),
]


# Systems of record (ADR-0100). Each case runs a copy of the guard in a scratch tree whose
# docs/governance/systems-of-record.yaml is the sample, a malformed file, or nothing.
_MALFORMED = "version: 1\nsystems:\n  - name: erp\n    binaries: [psql]\n"  # no owner
SOR_CASES: list[tuple[str, object, str, str]] = [
    ("sor · declared read passes", _bash('sf data query -q "SELECT Id FROM Account"'), "defer", "sample"),
    ("sor · write via binary asks", _bash("sf data delete record -s Account -i 1"), "ask", "sample"),
    ("sor · write via target asks", _bash('psql service=erp-prod -c "UPDATE t SET x=1"'), "ask", "sample"),
    ("sor · SELECT then DELETE asks", _bash('psql -h erp-prod -c "SELECT 1; DELETE FROM t"'), "ask", "sample"),
    ("sor · read piped to head passes", _bash('psql -h erp-prod -c "SELECT 1" | head -5'), "defer", "sample"),
    ("sor · POST to the ERP API asks", _bash("curl -X POST https://erp.example.internal/api/o"), "ask", "sample"),
    ("sor · undeclared database is free", _bash('psql -h localhost -c "DELETE FROM t"'), "defer", "sample"),
    ("sor · grep for a target is a read", _bash("grep -n erp-prod config.yml"), "defer", "sample"),
    ("sor · subagent write denied", _bash("sf data delete record -i 1", agent="phase-executor"), "deny", "sample"),
    ("sor · subagent read passes", _bash("sf org display", agent="phase-executor"), "defer", "sample"),
    # The guard fails open: a malformed declaration adds nothing. This case makes that visible.
    ("sor · malformed file fails open", _bash("sf data delete record -i 1"), "defer", "malformed"),
    ("sor · nothing declared, nothing new", _bash("sf data delete record -i 1"), "defer", "none"),
]


def _decide_with_declaration(payload: object, declaration: str) -> str:
    with tempfile.TemporaryDirectory() as root:
        hooks = Path(root) / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        guard = hooks / GUARD.name
        shutil.copy(GUARD, guard)
        if declaration != "none":
            target = Path(root) / "docs" / "governance" / SOR_DECLARATION.name
            target.parent.mkdir(parents=True)
            text = SOR_SAMPLE.read_text(encoding="utf-8") if declaration == "sample" else _MALFORMED
            target.write_text(text, encoding="utf-8")
        return _decide(payload, guard)


def _check_declaration() -> list[str]:
    """The guard ignores a malformed declaration; this is where it gets reported."""
    failures: list[str] = []
    spec = importlib.util.spec_from_file_location("high_risk_action_guard", GUARD)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    for path in (SOR_DECLARATION, SOR_SAMPLE):
        if not path.is_file():
            continue
        try:
            guard._parse_systems(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"{path.name} is malformed, so the guard ignores it: {exc}")
    return failures


def _check_wiring() -> list[str]:
    """Return a list of wiring failures (empty = OK)."""
    failures: list[str] = []
    if not GUARD.is_file():
        failures.append(f"guard script missing: {GUARD}")
    try:
        cfg = json.loads(SETTINGS.read_text())
        entries = cfg["hooks"]["PreToolUse"]
        matchers = " ".join(e.get("matcher", "") for e in entries)
        commands = " ".join(h.get("command", "") for e in entries for h in e.get("hooks", []))
        if "Bash" not in matchers:
            failures.append("settings.json: no PreToolUse matcher covers Bash")
        if "high-risk-action-guard.py" not in commands:
            failures.append("settings.json: PreToolUse does not invoke high-risk-action-guard.py")
    except Exception as exc:  # report any config problem as a failure
        failures.append(f"settings.json unreadable/invalid: {exc}")
    return failures


def main() -> int:
    print("F7 high-risk-action guard — verification\n" + "=" * 42)

    wiring = _check_wiring() + _check_declaration()
    for f in wiring:
        print(f"  FAIL  wiring: {f}")
    if not wiring:
        print("  PASS  wiring: settings.json registers the guard on Bash/Edit tools")

    print("-" * 42)
    failures = 0
    for desc, payload, expected in CASES:
        got = _decide(payload)
        ok = got == expected
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {desc:<40} expected={expected:<6} got={got}")
    for desc, payload, expected, declaration in SOR_CASES:
        got = _decide_with_declaration(payload, declaration)
        ok = got == expected
        failures += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {desc:<40} expected={expected:<6} got={got}")

    total = len(CASES) + len(SOR_CASES)
    print("-" * 42)
    print(
        f"{total - failures}/{total} decision checks passed; "
        f"wiring {'OK' if not wiring else 'FAILED'}."
    )
    if failures or wiring:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS  (logic + wiring verified)")
    print("\nNote: this verifies the guard's LOGIC and WIRING, not runtime activation.")
    print("To confirm it is live, restart Claude Code, approve the hook, then ask it to")
    print("run `git push --dry-run` — it should surface an 'ask' citing F7 / #133.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
