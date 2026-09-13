#!/usr/bin/env python3
"""Data-quality rules over the corpus's own datasets (issue #53).

specs/data/data-quality.md defines six dimensions, a rule shape and severities, and every row of
the data catalog read "none declared" — the datasets there belong to the adopting repository. But
this repository has datasets of its own: the spec registry, the ADR index, the four control
matrices and the adopter-path inventory. They have owners, they decay, and nothing measured them.

These are those rules, executed rather than tabulated. Each carries the fields the spec requires:
dataset, dimension, rule, measure, threshold, severity, on_violation.

  --run [--json]    evaluate every rule
  --list            print the rule table
Exit code is the number of rules violated at `critical` or `major`.
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "python"))

RULES = []


def rule(id, dataset, dimension, measure, threshold, severity, on_violation="alert"):
    def deco(fn):
        RULES.append({"id": id, "dataset": dataset, "dimension": dimension, "rule": fn.__doc__.strip(),
                      "measure": measure, "threshold": threshold, "severity": severity,
                      "on_violation": on_violation, "fn": fn})
        return fn
    return deco


def _specs():
    import build_spec_registry as reg
    return reg.collect()


def _adrs():
    return sorted(glob.glob(os.path.join(ROOT, "docs", "adr", "ADR-[0-9][0-9][0-9][0-9]-*.md")))


# ---- spec registry ------------------------------------------------------------------------------
@rule("DQ-REG-001", "spec-registry", "completeness",
      "count(specs on disk absent from the registry) / count(specs on disk)", "== 0", "critical", "block")
def reg_complete():
    """Every spec on disk appears in the registry."""
    import build_spec_registry as reg
    disk = {s["path"] for s in _specs()}
    data = json.load(open(os.path.join(ROOT, reg.JSON_PATH), encoding="utf-8"))
    have = {e["path"] for e in data.get("specs", [])}
    missing = sorted(disk - have)
    return (len(missing), f"{len(missing)} spec(s) missing: {', '.join(missing[:3])}" if missing else "")


@rule("DQ-REG-002", "spec-registry", "validity",
      "count(ids not matching ^SPEC-[A-Z][A-Z0-9]{1,5}-[0-9]{3}$)", "== 0", "critical", "block")
def reg_valid_ids():
    """Every registered spec id matches the ADR-0085 grammar."""
    import build_spec_registry as reg
    bad = [s["path"] for s in _specs() if not reg.ID_RE.match(s.get("id", ""))]
    return (len(bad), f"invalid ids: {bad[:3]}" if bad else "")


@rule("DQ-REG-003", "spec-registry", "uniqueness",
      "count((id, kind) pairs appearing on more than one non-superseded spec)", "== 0", "major")
def reg_unique_ids():
    """One live spec per (id, kind). ADR-0085 lets a subject carry a spec, a feature-spec and a
    threat-model under the same id, so uniqueness is per pair — the first version of this rule
    ignored kind and reported SPEC-LGS-001's three legitimate artefacts as a duplicate."""
    live = [s for s in _specs() if s.get("status") != "superseded"]
    pairs = Counter((s.get("id"), s.get("kind")) for s in live)
    dupes = [f"{i}/{k}" for (i, k), n in pairs.items() if n > 1]
    return (len(dupes), f"(id, kind) on multiple live specs: {dupes}" if dupes else "")


@rule("DQ-REG-004", "spec-registry", "consistency",
      "count(specs with status=superseded and no superseded_by)", "== 0", "major")
def reg_superseded_points_somewhere():
    """A superseded spec names its replacement, so the chain is walkable."""
    bad = [s["path"] for s in _specs()
           if s.get("status") == "superseded" and not s.get("superseded_by")]
    return (len(bad), f"superseded without a pointer: {bad}" if bad else "")


@rule("DQ-REG-005", "spec-registry", "timeliness",
      "count(specs whose last_updated is absent or not ISO-8601)", "== 0", "minor", "record")
def reg_dated():
    """Every spec carries a parseable last_updated date."""
    bad = [s["path"] for s in _specs()
           if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s.get("last_updated", "")))]
    return (len(bad), f"{len(bad)} spec(s) without a valid date" if bad else "")


@rule("DQ-REG-006", "spec-registry", "accuracy",
      "count(implemented specs with no verified_by entry)", "== 0", "major")
def reg_implemented_has_tests():
    """A spec marked implemented names what verifies it; otherwise the status is a claim."""
    bad = [s["path"] for s in _specs()
           if s.get("status") == "implemented" and not s.get("verified_by")]
    return (len(bad), f"implemented without verified_by: {bad[:3]}" if bad else "")


# ---- ADR index ----------------------------------------------------------------------------------
@rule("DQ-ADR-001", "adr-index", "completeness",
      "count(ADR files absent from docs/adr/README.md)", "== 0", "critical", "block")
def adr_indexed():
    """Every ADR on disk is linked from the index."""
    idx = open(os.path.join(ROOT, "docs", "adr", "README.md"), encoding="utf-8").read()
    missing = [os.path.basename(f) for f in _adrs() if os.path.basename(f) not in idx]
    return (len(missing), f"not indexed: {missing[:3]}" if missing else "")


@rule("DQ-ADR-002", "adr-index", "uniqueness",
      "count(duplicate ADR numbers)", "== 0", "critical", "block")
def adr_unique():
    """One number, one ADR."""
    nums = [os.path.basename(f)[4:8] for f in _adrs()]
    d = [n for n, c in Counter(nums).items() if c > 1]
    return (len(d), f"duplicates: {d}" if d else "")


@rule("DQ-ADR-003", "adr-index", "consistency",
      "count(gaps in the ADR numbering from 0001)", "== 0", "major")
def adr_contiguous():
    """ADR numbers run without gaps, so a missing number means a lost decision."""
    nums = sorted(int(os.path.basename(f)[4:8]) for f in _adrs())
    gaps = [n for n in range(1, (nums[-1] if nums else 0) + 1) if n not in nums]
    return (len(gaps), f"missing: {gaps[:5]}" if gaps else "")


@rule("DQ-ADR-004", "adr-index", "validity",
      "count(ADRs whose Status line is absent or not a known value)", "== 0", "major")
def adr_status():
    """Every ADR declares a status from the known vocabulary."""
    known = ("Proposed", "Accepted", "Deprecated", "Superseded")
    bad = []
    for f in _adrs():
        head = open(f, encoding="utf-8").read()[:2000]
        # Two formats are in use and both are valid: a "**Status:** X" line and a
        # "| **Status** | X |" table cell. The first version of this rule saw only the line and
        # reported five false positives — the rule was wrong, not the ADRs.
        m = (re.search(r"^\*\*Status:\*\*\s*(\w+)", head, re.M)
             or re.search(r"\|\s*\*\*Status\*\*\s*\|\s*(\w+)", head))
        if not m or m.group(1) not in known:
            bad.append(os.path.basename(f))
    return (len(bad), f"{len(bad)} ADR(s) with an unknown status: {bad[:3]}" if bad else "")


# ---- control matrices ---------------------------------------------------------------------------
@rule("DQ-MAT-001", "control-matrices", "completeness",
      "count(controls without an owner or a status)", "== 0", "critical", "block")
def mat_owned():
    """Every control names an owner and a status."""
    import check_control_matrix as ccm
    bad = 0
    for rel in ccm.DEFAULT_MATRICES:
        _, controls = ccm.parse_matrix(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        bad += sum(1 for c in controls if not c.get("owner") or not c.get("status"))
    return (bad, f"{bad} control(s) missing owner or status" if bad else "")


@rule("DQ-MAT-002", "control-matrices", "accuracy",
      "count(partial controls with no gap statement)", "== 0", "major")
def mat_gap():
    """A control marked partial says what is missing; otherwise the status carries no information."""
    import check_control_matrix as ccm
    bad = []
    for rel in ccm.DEFAULT_MATRICES:
        _, controls = ccm.parse_matrix(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        bad += [c.get("id") for c in controls
                if c.get("status") == "partial" and not (c.get("gap") or c.get("notes"))]
    return (len(bad), f"partial without a gap: {bad[:3]}" if bad else "")


@rule("DQ-MAT-003", "control-matrices", "timeliness",
      "count(matrices without a last_verified or version field)", "== 0", "minor", "record")
def mat_dated():
    """A control matrix records when it was last checked against its standard."""
    import check_control_matrix as ccm
    bad = []
    for rel in ccm.DEFAULT_MATRICES:
        top, _ = ccm.parse_matrix(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        if not (top.get("last_verified") or top.get("version")):
            bad.append(rel)
    return (len(bad), f"undated: {bad}" if bad else "")


# ---- adopter-path inventory ---------------------------------------------------------------------
@rule("DQ-ADP-001", "adopter-path-inventory", "completeness",
      "count(files naming an adopter path without the marker)", "== 0", "major")
def adp_marked():
    """Every file naming a path the adopting repository provides carries the marker."""
    import adopter_paths as ap
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        res = ap.scan()
        bad = [p for p, (_, marked) in res.items() if not marked]
    finally:
        os.chdir(cwd)
    return (len(bad), f"{len(bad)} unmarked: {bad[:3]}" if bad else "")


def evaluate():
    out = []
    for r in RULES:
        try:
            count, detail = r["fn"]()
            ok = count == 0
        except Exception as e:  # a rule that cannot run is a violation, not a pass
            count, detail, ok = -1, f"rule failed to evaluate: {e}", False
        out.append({k: r[k] for k in ("id", "dataset", "dimension", "severity", "on_violation",
                                      "rule", "measure", "threshold")} | {"violations": count, "ok": ok, "detail": detail})
    return out


def main():
    ap_ = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap_.add_argument("--run", action="store_true")
    ap_.add_argument("--list", action="store_true")
    ap_.add_argument("--json", action="store_true")
    ap_.add_argument("--quiet", action="store_true")
    a = ap_.parse_args()

    if a.list:
        print(f"{'id':<14}{'dataset':<24}{'dimension':<14}{'severity':<10}rule")
        for r in RULES:
            print(f"{r['id']:<14}{r['dataset']:<24}{r['dimension']:<14}{r['severity']:<10}{r['rule']}")
        return 0

    results = evaluate()
    if a.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    failed = [r for r in results if not r["ok"]]
    blocking = [r for r in failed if r["severity"] in ("critical", "major")]
    if not a.json:
        if not a.quiet:
            by_ds = Counter(r["dataset"] for r in results)
            print(f"data quality: {len(results)} rules over {len(by_ds)} corpus datasets")
        for r in failed:
            print(f"  {r['severity'].upper():<8} {r['id']} [{r['dataset']}/{r['dimension']}] "
                  f"{r['violations']} violation(s) — {r['detail']}")
        if not failed and not a.quiet:
            print(f"  all {len(results)} rules pass")
    return len(blocking)


if __name__ == "__main__":
    sys.exit(main())
