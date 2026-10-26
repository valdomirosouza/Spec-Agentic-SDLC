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

# The scope is DERIVED, not listed. The first version of this check carried four names written by
# hand, and a hand-written list is complete only where someone looked: it missed
# .claude/skills/deliver/SKILL.md, which held a whole second class-to-tier mapping under the
# heading "one mapping" — the very duplication this check exists to prevent. That was the fifth
# time this corpus was bitten by a set chosen by enumeration, and the first time inside the guard
# against the defect (R15-T1).
#
# A file is in scope when it names at least two risk classes. Exemptions are DECLARED by the
# marker below, never inferred from a name — deriving the scope and declaring the exemptions are
# the two halves that have to go together, because a derived scope with no escape gets loosened
# until it catches nothing.
IN_SCOPE_MIN_LABELS = 2
EXEMPT_MARKER = "risk-classes: not a restatement"

# Historical spellings. A file using one of these is restating the vocabulary in the old words,
# which is exactly what has to be caught — matching only the current labels would call a stale
# file compliant by failing to recognise it.
VARIANTS = ("small fix", "security-sensitive", "infrastructure/platform", "ai/llm/agentic")

# The one file allowed to carry a class-to-tier mapping.
ARBITER = "docs/process/gates/phase-gates.yaml"
TIERS = ("TRIVIAL", "STANDARD", "GOVERNED", "REGULATED")


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


def in_scope():
    """Every file that restates the vocabulary, derived — plus the ones that declared an escape."""
    hits, exempt = [], []
    classes, _, _ = declared()
    labels = [l.lower() for _, l, _, _ in classes]
    for d, dn, fn in os.walk(ROOT):
        dn[:] = [x for x in dn if x not in (".git", ".serena", ".sdd", "node_modules")]
        for f in fn:
            if not f.endswith((".md", ".yaml", ".yml", ".toml")):
                continue
            rel = os.path.relpath(os.path.join(d, f), ROOT)
            if rel.startswith("docs/reference/") or rel in ("CHANGELOG.md", ARBITER):
                continue
            with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            low = text.lower()
            n = sum(1 for l in labels if l in low) + sum(1 for v in VARIANTS if v in low)
            if n < IN_SCOPE_MIN_LABELS:
                continue
            (exempt if EXEMPT_MARKER in text else hits).append((rel, text))
    return hits, exempt


def problems():
    out = []
    classes, tiers, phases = declared()
    if not classes:
        return ["phase-gates.yaml declares no risk_classes"]
    for cid, label, tier, adds in classes:
        if tier not in tiers:
            out.append(f"risk class {cid} names a minimum_tier {tier} that phase-gates.yaml does "
                       f"not define")
        for p in adds:
            if p not in phases:
                out.append(f"risk class {cid} forces phase {p}, which does not exist")

    labels = [label for _, label, _, _ in classes]
    scoped, _ = in_scope()
    for rel, text in scoped:
        low = text.lower()
        stale = [v for v in VARIANTS if v in low and
                 not any(v in l.lower() for l in labels)]
        if stale:
            out.append(f"{rel}: uses the historical spelling(s) {', '.join(sorted(set(stale)))} "
                       f"instead of the declared labels")
        # A second class-to-tier mapping: the file names classes AND tiers. Only the arbiter may.
        if sum(1 for t in TIERS if re.search(rf'\b{t}\b', text)) >= 2 and \
                sum(1 for l in labels if l.lower() in low) >= 2:
            out.append(f"{rel}: carries a second class-to-tier mapping — the tier a class floors "
                       f"at is data, and {ARBITER} is its arbiter (ADR-0095 §2)")
        if re.search(r'canonical Risk-Based Flow table', text, re.I) and rel != CANON:
            out.append(f"{rel}: calls its own copy of the flow table canonical")

    # The other direction, and it is not symmetry for its own sake. Deriving the scope from the
    # labels means a label renamed in the arbiter alone is invisible: the documents keep the old
    # word, the new word is nowhere, and every document stays in scope on the strength of the five
    # labels that did not change. Requiring each declared label to be used somewhere is what makes
    # the rename visible — the mutation proof for this check failed exactly here (R15-T1).
    used = "\n".join(t for _, t in scoped).lower()
    orphan = [l for l in labels if l.lower() not in used]
    if orphan:
        out.append(f"declared label(s) {', '.join(orphan)} appear in no document that restates "
                   f"the vocabulary — renamed in the arbiter and nowhere else")
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
            scoped, exempt = in_scope()
            extra = f", {len(exempt)} exempt by marker" if exempt else ""
            print(f"{len(classes)} risk classes, each flooring at one of {len(tiers)} tiers, "
                  f"restated identically in {len(scoped)} document(s) found by scanning{extra}")
    if a.check and probs:
        for p in probs:
            print(p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
