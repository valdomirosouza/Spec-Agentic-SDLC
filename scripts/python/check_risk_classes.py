"""One vocabulary of risk classes, declared in one place (#110).

The corpus carried two unrelated classification systems — six risk classes in prose and four tiers
in the gate data — with no mapping between them, and four documents restated the six classes from
memory. Two of the four were already wrong: `DEFINITION_OF_READY.md` called the first class "small
fix", and `.claude/agents/asdd-orchestrator.md` merged three classes into one, dropped the
distinctions, and called its own four-row copy "the canonical Risk-Based Flow table".

The copy an agent executes was the wrong one. That is the whole cost of an uncontrolled vocabulary:
it is not that the words differ, it is that the authority moves to whichever copy was read last.

`risk_classes` in docs/process/gates/phase-gates.yaml is the declaration (ADR-0095 §2 makes that
file the arbiter for gate data). This check requires:

  tiers      every class names a tier that exists in the same file
  phases     every phase a class forces exists
  labels     every document that restates the classes uses the declared labels, all of them
  canon      no file outside the canonical narrative calls its own copy canonical

    check_risk_classes.py [--check] [--quiet]
"""
import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GATES = os.path.join(ROOT, "docs", "process", "gates", "phase-gates.yaml")
CANON = "docs/sdlc/agentic-spec-driven-delivery.md"

# Documents that restate the vocabulary for a reader or an agent. Listed, not detected: a file that
# happens to contain the words "small bug fix" is not thereby a restatement, and guessing which
# files are normative from their content is the shape-based reasoning this corpus keeps rejecting.
RESTATEMENTS = (
    CANON,
    "docs/process/DEFINITION_OF_READY.md",
    ".claude/agents/asdd-phase-0-intake.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
)


def declared():
    """([(id, label, tier, adds)], [tier ids], [phase ids]) from the arbiter."""
    with open(GATES, encoding="utf-8") as fh:
        text = fh.read()
    block = text[text.index("risk_classes:"):text.index("spec_for_defect:")]
    classes = []
    for chunk in re.split(r'\n  - id: ', block)[1:]:
        cid = chunk.split("\n")[0].strip()
        label = re.search(r'label: (.*)', chunk).group(1).strip()
        tier = re.search(r'tier: (\S+)', chunk).group(1).strip()
        adds = re.search(r'adds: \[([^\]]*)\]', chunk)
        adds = [int(x) for x in adds.group(1).split(",") if x.strip()] if adds else []
        classes.append((cid, label, tier, adds))
    tiers = re.findall(r'^  - id: ([A-Z]+)$', text[text.index("\ntiers:"):], re.M)
    phases = [int(p) for p in re.findall(r'^  - id: (\d+)$', text[text.index("\nphases:"):], re.M)]
    return classes, tiers, phases


def problems():
    out = []
    classes, tiers, phases = declared()
    if not classes:
        return ["phase-gates.yaml declares no risk_classes"]
    for cid, label, tier, adds in classes:
        if tier not in tiers:
            out.append(f"risk class {cid} names tier {tier}, which phase-gates.yaml does not define")
        for p in adds:
            if p not in phases:
                out.append(f"risk class {cid} forces phase {p}, which does not exist")

    labels = [label for _, label, _, _ in classes]
    for rel in RESTATEMENTS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            out.append(f"{rel}: restates the risk classes but is gone")
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read().lower()
        absent = [l for l in labels if l.lower() not in text]
        if absent:
            out.append(f"{rel}: does not use the declared label(s) {', '.join(absent)}")

    # A second copy that calls itself canonical is how the authority moved last time.
    for d, dn, fn in os.walk(ROOT):
        dn[:] = [x for x in dn if x not in (".git", ".serena", ".sdd", "node_modules")]
        for f in fn:
            if not f.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(d, f), ROOT)
            # CHANGELOG.md records what was removed, and a changelog that may not quote the
            # sentence it deleted cannot describe the deletion. Named, with the reason, rather
            # than widened into "files that only mention it" — the rule that fires on a quotation
            # is the rule that gets relaxed until it fires on nothing.
            if rel in (CANON, "CHANGELOG.md") or rel.startswith("docs/reference/"):
                continue
            with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                if re.search(r'canonical Risk-Based Flow table', fh.read(), re.I):
                    out.append(f"{rel}: calls its own copy of the flow table canonical")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    probs = problems()
    if not a.quiet:
        if probs:
            print("\n".join(probs))
        else:
            classes, tiers, _ = declared()
            print(f"{len(classes)} risk classes, each mapped to one of {len(tiers)} tiers, "
                  f"restated identically in {len(RESTATEMENTS)} documents")
    if a.check and probs:
        for p in probs:
            print(p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
