#!/usr/bin/env python3
"""Declared "not applicable" checks for check-corpus.sh (ADR-0098).

An adopting repository whose shape differs from a service declares, in
docs/governance/applicability-matrix.yml, the checks that do not apply to it:

    adoption_profile: batch-data        # service (default) | batch-data
    not_applicable:
      - check: "<name exactly as check-corpus.sh prints it>"
        reason: "<why it does not apply>"
        owner: "<who answers for it>"
        review_by: "YYYY-MM-DD"

A declaration is one of:
  active    the check's failure is printed as `n/a: <reason>` and not counted
  expired   `review_by` has passed: the check counts again
  refused   the check enforces a protected Constitution article or the verifier's own integrity
  invalid   a missing field, a bad date, or a name check-corpus.sh does not print

  not_applicable.py --tsv     state, check, reason, owner, review_by per line (read by check-corpus.sh)
  not_applicable.py --check   exit 1 on a refused or invalid declaration or an unknown profile

The file uses a small, regular subset of YAML, parsed here so the corpus runs on a bare Python 3.
"""
import datetime
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MATRIX = os.path.join("docs", "governance", "applicability-matrix.yml")
VERIFIER = os.path.join("scripts", "bash", "check-corpus.sh")
PROFILES = ("service", "batch-data")
FIELDS = ("check", "reason", "owner", "review_by")

# Never declarable. A check here enforces a protected Constitution article (I, II, V, VII, IX), or
# keeps the verifier honest. Declaring one fails the run (ADR-0098 §3). A new check that enforces a
# protected article belongs on this list.
REFUSED = {
    # I  Specification first
    "frontmatter": "I",
    "spec registry matches disk": "I",
    "check-prerequisites keeps --require-approved (approved|implemented only)": "I",
    "tests/hooks/test_sdd_gate.py": "I",
    # II Test-backed change
    "tasks-template keeps tests-first and mandatory tests": "II",
    "ADR-0022 declares exactly one floor": "II",
    "constitution and CLAUDE.md reference the floor, not a bare number": "II",
    # V  Human oversight of agents
    "verify-high-risk-guard": "V",
    "settings.json keeps the PreToolUse high-risk guard": "V",
    "vcs.sh refuses merge, release, deploy, push and protected branches": "V",
    "only vcs.sh creates a branch, and only behind the protected-name guard": "V",
    "scripts never push/merge/commit/rebase/reset/switch": "V",
    "asdd_state.py runs no git or gh": "V",
    "gates: 13 blocking, 9 requiring a human": "V",
    "red-team RT-2026-09-13 findings stay closed": "V",
    # VII Traceability and auditability
    "adr-index": "VII",
    "changed scripts and contracts are recorded in the changelog": "VII",
    "constitution has articles I–IX and a version line": "VII",
    # the verifier's own integrity
    "every named check has a failing path": "verifier",
    "mutation coverage has not fallen": "verifier",
    "declared n/a are valid": "verifier",
}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _value(raw):
    raw = raw.split(" #", 1)[0].strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1]
    return raw


def parse(text):
    """(profile or None, [entry dict]) from the matrix text."""
    profile = None
    entries = []
    m = re.search(r"^adoption_profile:\s*(.*)$", text, re.M)
    if m:
        profile = _value(m.group(1))
    block = re.search(r"^not_applicable:[ \t]*(.*)\n((?:[ \t]+.*\n?|\n)*)", text, re.M)
    if not block or block.group(1).strip().startswith("[]"):
        return profile, entries
    for line in block.group(2).split("\n"):
        item = re.match(r"^\s*-\s+(\w+):\s*(.*)$", line)
        field = re.match(r"^\s+(\w+):\s*(.*)$", line)
        if item:
            entries.append({item.group(1): _value(item.group(2))})
        elif field and entries:
            entries[-1][field.group(1)] = _value(field.group(2))
    return profile, entries


def check_names(root):
    """Every name check-corpus.sh can print, so a typo cannot silence nothing and look fine."""
    try:
        text = open(os.path.join(root, VERIFIER), encoding="utf-8").read()
    except OSError:
        return None
    return set(re.findall(r'result "([^"$]+)"', text))


def classify(entry, names, today):
    missing = [f for f in FIELDS if not entry.get(f)]
    if missing:
        return "invalid", f"missing {', '.join(missing)}"
    if entry["check"] in REFUSED:
        what = REFUSED[entry["check"]]
        return "refused", "keeps the verifier honest" if what == "verifier" else f"enforces Article {what}"
    if names is not None and entry["check"] not in names:
        return "invalid", "check-corpus.sh prints no check by that name"
    if not DATE.match(entry["review_by"]):
        return "invalid", "review_by is not YYYY-MM-DD"
    try:
        due = datetime.date.fromisoformat(entry["review_by"])
    except ValueError:
        return "invalid", "review_by is not a real date"
    return ("expired", f"review_by {entry['review_by']} has passed") if due < today else ("active", "")


def declarations(root=ROOT, today=None):
    """(profile, [(state, why, entry)]). An absent matrix declares nothing."""
    today = today or datetime.date.today()
    try:
        text = open(os.path.join(root, MATRIX), encoding="utf-8").read()
    except OSError:
        return None, []
    profile, entries = parse(text)
    names = check_names(root)
    return profile, [(*classify(e, names, today), e) for e in entries]


def problems(root=ROOT, today=None):
    profile, decls = declarations(root, today)
    out = []
    if profile is not None and profile not in PROFILES:
        out.append(f"adoption_profile {profile!r} is not one of {', '.join(PROFILES)}")
    for state, why, e in decls:
        if state in ("refused", "invalid"):
            out.append(f"{e.get('check') or '(no check)'}: {state} — {why}")
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = os.getcwd()
    if "--tsv" in argv:
        for state, why, e in declarations(root)[1]:
            print("\t".join([state, e.get("check", ""), e.get("reason", ""), e.get("owner", ""), e.get("review_by", "")]))
        return 0
    if "--check" in argv:
        profile, decls = declarations(root)
        bad = problems(root)
        active = [d for d in decls if d[0] == "active"]
        expired = [d for d in decls if d[0] == "expired"]
        print(f"profile {profile or 'service'}; {len(active)} active, {len(expired)} expired, {len(bad)} rejected")
        for b in bad:
            print(f"  {b}")
        for _, _, e in active:
            print(f"  n/a: {e['check']} — {e['reason']} (owner {e['owner']}, review by {e['review_by']})")
        for _, why, e in expired:
            print(f"  expired: {e['check']} — {why}; the check counts again")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
