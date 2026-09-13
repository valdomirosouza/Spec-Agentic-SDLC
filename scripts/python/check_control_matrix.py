#!/usr/bin/env python3
"""Validate the control matrices of this corpus (issue #43).

Several documents cite `scripts/governance/check_control_matrix.py` as the gate that keeps the
matrices honest. That script lives in the product template, not here, so nothing has been checking
them: the OWASP matrix header promises that every implemented_by / verified_by path exists, and
that promise was unverified.

Checks, per YAML matrix:
  M1  parses, and has the `standard`, `version` and `controls` keys
  M2  every control has a unique, non-empty `id`
  M3  every control has `owner` and `status`
  M4  `status` is in the allowed vocabulary
  M5  a control whose status is `n/a` carries a `justification`
  M6  a control whose status is `partial` carries a `gap`
  M7  every corpus path in implemented_by / verified_by exists on disk
      - `adopter:<path>`  is the adopting repository's, and is not checked for existence
      - `ci:<job>`        is a CI job name, not a path
      - `planned:#<n>:<path>` must name an issue and is reported so it cannot be forgotten
  M8  no control is missing evidence entirely unless its status is `n/a` or `prohibited`

And for the Markdown ISO/IEC 42001 matrix: all nine Annex A objectives A.2 to A.10 are present.

No third-party dependency: the matrices use a small, regular subset of YAML and this module parses
exactly that subset, so `check-corpus.sh` runs with a bare Python 3.

Usage: check_control_matrix.py [--quiet] [<matrix.yaml> ...]
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_MATRICES = [
    "specs/security/asvs-control-matrix.yaml",
    "specs/security/owasp-genai-control-matrix.yaml",
    "specs/compliance/eu-ai-act-control-matrix.yaml",
]
ISO42001_MATRIX = "docs/compliance/iso42001-annex-a-control-matrix.md"
STATUSES = {"implemented", "partial", "planned", "n/a", "prohibited"}
EVIDENCE_KEYS = ("implemented_by", "verified_by")


def parse_matrix(text):
    """Parse the control-matrix subset of YAML: top-level scalars plus a `controls:` list whose
    entries have scalar fields, block scalars (>- and |) and simple string lists."""
    top, controls = {}, []
    lines = text.split("\n")
    i, n = 0, len(lines)
    cur = None
    in_controls = False
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = len(line) - len(line.lstrip())

        if indent == 0 and stripped == "controls:":
            in_controls = True
            i += 1
            continue
        if indent == 0 and not in_controls:
            m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", stripped)
            if m:
                top[m.group(1)] = m.group(2).strip()
            i += 1
            continue
        if not in_controls:
            i += 1
            continue

        if stripped.startswith("- ") and indent <= 2:
            cur = {"_line": i + 1}
            controls.append(cur)
            stripped = stripped[2:].strip()
            indent += 2

        if cur is None:
            i += 1
            continue

        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", stripped)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()

        if val in (">-", ">", "|", "|-"):  # block scalar: consume deeper-indented lines
            buf = []
            i += 1
            while i < n:
                nxt = lines[i]
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= indent:
                    break
                buf.append(nxt.strip())
                i += 1
            cur[key] = " ".join(buf).strip()
            continue

        if val == "":  # possible list
            items, j = [], i + 1
            while j < n:
                nxt = lines[j]
                s = nxt.strip()
                if not s or s.startswith("#"):
                    j += 1
                    continue
                ind = len(nxt) - len(nxt.lstrip())
                if ind <= indent or not s.startswith("- "):
                    break
                items.append(s[2:].strip().strip('"').strip("'"))
                j += 1
            cur[key] = items
            i = j
            continue

        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            cur[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner else []
            i += 1
            continue

        cur[key] = val.strip('"').strip("'")
        i += 1
    return top, controls


def check_matrix(rel, quiet=False):
    path = os.path.join(ROOT, rel)
    errs, notes = [], []
    if not os.path.isfile(path):
        return [f"{rel}: missing"], []
    top, controls = parse_matrix(open(path, encoding="utf-8").read())

    for k in ("standard", "version"):                                            # M1
        if not top.get(k):
            errs.append(f"{rel}: missing top-level `{k}`")
    if not controls:
        errs.append(f"{rel}: no controls parsed")
        return errs, notes

    seen = {}
    for c in controls:
        line = c.get("_line", "?")
        cid = c.get("id", "")
        if not cid:                                                              # M2
            errs.append(f"{rel}:{line}: control with no id")
            continue
        if cid in seen:
            errs.append(f"{rel}:{line}: duplicate id `{cid}` (first at line {seen[cid]})")
        seen[cid] = line

        if not c.get("owner"):                                                   # M3
            errs.append(f"{rel}:{line}: `{cid}` has no owner")
        status = c.get("status", "")
        if not status:
            errs.append(f"{rel}:{line}: `{cid}` has no status")
        elif status not in STATUSES:                                             # M4
            errs.append(f"{rel}:{line}: `{cid}` status `{status}` not in {sorted(STATUSES)}")
        if status == "n/a" and not c.get("justification"):                       # M5
            errs.append(f"{rel}:{line}: `{cid}` is n/a without a justification")
        if status == "partial" and not (c.get("gap") or c.get("notes")):         # M6
            errs.append(f"{rel}:{line}: `{cid}` is partial without a gap")

        evidence = []
        for key in EVIDENCE_KEYS:
            v = c.get(key, [])
            evidence += v if isinstance(v, list) else [v]
        for e in evidence:                                                       # M7
            if not e:
                continue
            if e.startswith("ci:"):
                continue
            if e.startswith("adopter:"):
                continue
            m = re.match(r"^planned:#(\d+):(.+)$", e)
            if m:
                notes.append(f"{rel}:{line}: `{cid}` cites planned issue #{m.group(1)} for {m.group(2)}")
                continue
            if not os.path.exists(os.path.join(ROOT, e)):
                errs.append(f"{rel}:{line}: `{cid}` cites a path that does not exist: {e}")
        if not evidence and status not in ("n/a", "prohibited"):                 # M8
            errs.append(f"{rel}:{line}: `{cid}` has status `{status}` and no evidence")

    if not quiet:
        by_status = {}
        for c in controls:
            by_status[c.get("status", "?")] = by_status.get(c.get("status", "?"), 0) + 1
        summary = " · ".join(f"{k}: {v}" for k, v in sorted(by_status.items()))
        print(f"  {rel}: {len(controls)} controls — {summary}")
    return errs, notes


def check_iso42001(quiet=False):
    path = os.path.join(ROOT, ISO42001_MATRIX)
    if not os.path.isfile(path):
        return [f"{ISO42001_MATRIX}: missing"], []
    text = open(path, encoding="utf-8").read()
    missing = [f"A.{i}" for i in range(2, 11) if f"**A.{i}**" not in text]
    if not quiet:
        print(f"  {ISO42001_MATRIX}: {9 - len(missing)}/9 Annex A objectives present")
    return ([f"{ISO42001_MATRIX}: objectives not found: {', '.join(missing)}"] if missing else []), []


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    matrices = args or DEFAULT_MATRICES
    all_errs, all_notes = [], []
    if not quiet:
        print("control matrices:")
    for rel in matrices:
        e, nt = check_matrix(rel, quiet)
        all_errs += e
        all_notes += nt
    if not args:
        e, nt = check_iso42001(quiet)
        all_errs += e
        all_notes += nt
    for nt in all_notes:
        print(f"  note: {nt}")
    for e in all_errs:
        print(f"  ERROR {e}")
    if all_errs:
        print(f"control-matrix check: {len(all_errs)} error(s)")
        return 1
    if not quiet:
        print("control-matrix check: all matrices valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
