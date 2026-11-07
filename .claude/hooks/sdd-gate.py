#!/usr/bin/env python3
"""UserPromptSubmit gate for the code-producing /sdd-* commands (ADR-0092 decision 1, issue #22).

Deterministic and read-only. When the submitted prompt *starts* with /sdd-plan, /sdd-tasks,
/sdd-implement or /sdd-taskstoissues:
  * spec of the active feature not `approved`/`implemented`  -> exit 2 (prompt blocked; stderr is
    the message) -- Constitution I becomes a harness rule, not only a prompt rule;
  * otherwise a checklist table (checked/unchecked per checklists/*.md) is printed to stdout, which
    Claude Code adds as context; unchecked items remain a "proceed anyway?" question for a human.
When it starts with `/sdd-bugfix fix BUG-<issue>` (ADR-0096), the stage that edits code:
  * docs/bugs/BUG-<issue>/assessment.md missing, its Decision table's last filled row not
    `accepted`, or its `**Spec:**` line naming neither an approved/implemented spec nor a
    `REM-NNN`                                               -> exit 2;
  * otherwise a one-line confirmation is printed as context.
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
BUGFIX_FIX = re.compile(r"^\s*/sdd-bugfix\s+fix\b(?:\s+BUG-(\d+)\b)?")
SPEC_LINE = re.compile(r"^\*\*Spec:\*\*\s*`?([^`\s]+)`?", re.M)
REM_ID = re.compile(r"^REM-\d{3,}$")


def fm_field(path, key):
    """The frontmatter value of `key`, as scripts/bash/common.sh fm_field reads it."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0] != "---":
        return ""
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith(key + ":"):
            return re.sub(r"\s*#.*", "", line[len(key) + 1:]).strip()
    return ""


def decision(text):
    """The decision cell of the last filled row of the assessment's Decision table, lower-cased."""
    m = re.search(r"^#+ .*Decision.*$", text, re.M)
    if not m:
        return ""
    last = ""
    for line in text[m.end():].splitlines():
        line = line.strip()
        if line.startswith("#"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")] if line.startswith("|") else []
        if len(cells) < 3 or cells[0].lower() == "decided by" or set(cells[0]) <= set("-: "):
            continue
        if cells[0] and not cells[0].startswith("{"):
            last = cells[2].lower()
    return last


def bugfix_gate(root, bug):
    """(exit code, message) for `/sdd-bugfix fix BUG-<bug>`; the ADR-0096 preconditions."""
    if bug is None:
        return 0, ("[sdd-gate] /sdd-bugfix fix: no BUG-<issue> given, so the preconditions were not "
                   "checked. The command will stop at its own precondition check.")
    rel = os.path.join("docs", "bugs", f"BUG-{bug}", "assessment.md")
    path = os.path.join(root, rel)
    if not os.path.isfile(path):
        return 2, (f"[sdd-gate] /sdd-bugfix fix blocked: {rel} does not exist. Run "
                   f"`/sdd-bugfix assess` first; the fix stage starts from an accepted diagnosis (ADR-0096).")
    text = open(path, encoding="utf-8").read()
    verdict = decision(text)
    if verdict != "accepted":
        shown = verdict or "no decision recorded"
        return 2, (f"[sdd-gate] /sdd-bugfix fix blocked: the Decision table of {rel} reads '{shown}'. "
                   f"A person accepts the diagnosis before any code changes (ADR-0096, Constitution V).")
    m = SPEC_LINE.search(text)
    ref = m.group(1) if m else ""
    if REM_ID.match(ref):
        return 0, f"[sdd-gate] /sdd-bugfix fix: BUG-{bug} diagnosis accepted; remediation {ref}."
    spec = os.path.realpath(os.path.join(root, ref)) if ref else ""
    specs_dir = os.path.realpath(os.path.join(root, "specs")) + os.sep
    if not ref or not spec.startswith(specs_dir) or not os.path.isfile(spec):
        return 2, (f"[sdd-gate] /sdd-bugfix fix blocked: {rel} has no `**Spec:**` line naming a spec "
                   f"under specs/ or a REM-NNN (found '{ref}'). The fix cites the spec it restores "
                   f"(spec_for_defect, Constitution I).")
    status = fm_field(spec, "status")
    if status not in ("approved", "implemented"):
        return 2, (f"[sdd-gate] /sdd-bugfix fix blocked: the cited spec {ref} has status '{status}'. "
                   f"Code is fixed against an approved spec (Constitution I, ADR-0085, ADR-0096).")
    return 0, f"[sdd-gate] /sdd-bugfix fix: BUG-{bug} diagnosis accepted; spec {ref} is {status}."


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    prompt = payload.get("user_prompt") or payload.get("prompt") or ""
    root = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    b = BUGFIX_FIX.match(prompt)
    if b:
        try:
            rc, msg = bugfix_gate(root, b.group(1))
        except Exception:
            return 0
        if rc:
            sys.stderr.write(msg + "\n")
        else:
            print(msg)
        return rc
    m = LEADING.match(prompt)
    if not m or m.group(1) not in COMMANDS:
        return 0
    cmd = m.group(1)
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
