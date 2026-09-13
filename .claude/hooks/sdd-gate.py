#!/usr/bin/env python3
"""UserPromptSubmit gate for the code-producing /sdd-* commands (ADR-0092 decision 1, issue #22).

Deterministic and read-only. When the submitted prompt *starts* with /sdd-plan, /sdd-tasks,
/sdd-implement or /sdd-taskstoissues:
  * spec of the active feature not `approved`/`implemented`  -> exit 2 (prompt blocked; stderr is
    the message) -- Constitution I becomes a harness rule, not only a prompt rule;
  * otherwise a checklist table (checked/unchecked per checklists/*.md) is printed to stdout, which
    Claude Code adds as context; unchecked items remain a "proceed anyway?" question for a human.
Any other prompt, any error, any missing script -> exit 0 with no output (fails open, never edits
files, never runs git). Mentioning a command mid-sentence does not trigger the gate.
"""
import glob
import json
import os
import re
import subprocess
import sys

COMMANDS = ("sdd-plan", "sdd-tasks", "sdd-implement", "sdd-taskstoissues")
LEADING = re.compile(r"^\s*/(sdd-[a-z]+)\b")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = payload.get("user_prompt") or payload.get("prompt") or ""
    m = LEADING.match(prompt)
    if not m or m.group(1) not in COMMANDS:
        return 0
    cmd = m.group(1)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    script = os.path.join(root, "scripts", "bash", "check-prerequisites.sh")
    if not os.path.isfile(script):
        return 0
    try:
        r = subprocess.run(["bash", script, "--json", "--require-spec"], cwd=root,
                           capture_output=True, text=True, timeout=5)
    except Exception:
        return 0
    if r.returncode != 0:
        detail = (r.stderr.strip().splitlines() or [""])[-1]
        print(f"[sdd-gate] /{cmd}: no active feature spec resolved — {detail} "
              f"The command will stop at its own prerequisite check.")
        return 0
    try:
        info = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return 0
    spec_id = info.get("SPEC_ID", "?")
    status = info.get("SPEC_STATUS", "")
    if status not in ("approved", "implemented"):
        sys.stderr.write(
            f"[sdd-gate] /{cmd} blocked: spec {spec_id} has status '{status}'. Code-producing "
            f"commands need an approved spec (Constitution I, ADR-0085, ADR-0092). Approve it via "
            f"Spec-as-PR, then retry.\n")
        return 2
    rows = []
    unchecked_total = 0
    for f in sorted(glob.glob(os.path.join(info.get("FEATURE_DIR", ""), "checklists", "*.md"))):
        try:
            text = open(f, encoding="utf-8").read()
        except Exception:
            continue
        checked = len(re.findall(r"^- \[[xX]\]", text, re.M))
        unchecked = len(re.findall(r"^- \[ \]", text, re.M))
        unchecked_total += unchecked
        rows.append((os.path.basename(f), checked + unchecked, checked, unchecked))
    lines = [f"[sdd-gate] /{cmd}: spec {spec_id} is {status}."]
    if rows:
        lines += ["| checklist | items | checked | unchecked |", "|---|---|---|---|"]
        lines += [f"| {n} | {t} | {c} | {u} |" for n, t, c, u in rows]
        lines.append(
            "Unchecked items are reviewer decisions: stop and ask \"proceed anyway?\" before "
            "producing code, and never tick them (ADR-0092)." if unchecked_total
            else "All checklist items are checked.")
    else:
        lines.append("No checklists/ found for this feature — /sdd-specify normally creates checklists/requirements.md.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
