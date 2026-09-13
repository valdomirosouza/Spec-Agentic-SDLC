#!/usr/bin/env python3
"""How much of check-corpus.sh has been proved able to fail, and a ratchet on that number (#75).

The mutation harness answers "can this check fail when fed its own defect". It answered that for
14 of 46 named checks and nothing asked about the other 32, so anyone could add check 47 with no
proof at all and the build would stay green. That is the round-5 finding one level up: the
verifier became partly verified, and the verification of the verifier had no guard.

The shape is borrowed from the corpus's own test-integrity gate (ADR-0065): a versioned baseline,
a failure when the number falls, and a deliberate, visible act to move it. It does not demand
46 of 46 today. It demands that the number never quietly go down.

    mutation_coverage.py            # report coverage and list what is unproved
    mutation_coverage.py --check    # fail if coverage fell below the baseline
    mutation_coverage.py --update   # record the current numbers as the new baseline
"""
import argparse
import ast
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VERIFIER = os.path.join(ROOT, "scripts", "bash", "check-corpus.sh")
HARNESS = os.path.join(ROOT, "tests", "scripts", "test_check_corpus.py")
BASELINE = os.path.join(ROOT, "tests", ".mutation-coverage-baseline.json")

_RESULT = re.compile(r'\bresult\s+"([^"]+)"')


def named_checks():
    """Every distinct check name check-corpus.sh can print. One name may be printed from both the
    ok and the fail branch, so they are de-duplicated."""
    with open(VERIFIER, encoding="utf-8") as fh:
        return sorted(set(_RESULT.findall(fh.read())))


def proved_names():
    """The `check_name` argument of every assert_mutation_is_caught call.

    Parsed from the syntax tree rather than matched with a regular expression: the second argument
    sits after a multi-line first argument in most calls, and a pattern loose enough to reach it
    would also match unrelated strings in the same call."""
    with open(HARNESS, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), HARNESS)
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name != "assert_mutation_is_caught" or len(node.args) < 2:
            continue
        arg = node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            out.append(arg.value)
    return sorted(set(out))


def coverage():
    """Which named checks a mutation covers.

    A harness entry names a check by the same substring the harness matches against the failure
    line, so the mapping here has to use that same rule — anything stricter would report checks as
    unproved that the harness does in fact prove."""
    names, proofs = named_checks(), proved_names()
    covered, orphan = set(), []
    for p in proofs:
        hits = [n for n in names if p in n]
        if hits:
            covered.update(hits)
        else:
            orphan.append(p)
    return {
        "named": len(names),
        "proved": len(covered),
        "mutations": len(proofs),
        "unproved": sorted(set(names) - covered),
        "orphan_mutations": orphan,
    }


def read_baseline():
    if not os.path.isfile(BASELINE):
        return None
    with open(BASELINE, encoding="utf-8") as fh:
        return json.load(fh)


def write_baseline(c):
    payload = {
        "_comment": "Mutation coverage ratchet (#75). Raise it by proving more checks; lowering it "
                    "is a deliberate act that belongs in a commit message, not a side effect.",
        "named": c["named"],
        "proved": c["proved"],
    }
    with open(BASELINE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return payload


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if coverage fell below the baseline")
    ap.add_argument("--update", action="store_true", help="record current coverage as the baseline")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    c = coverage()

    if a.update:
        p = write_baseline(c)
        print(f"baseline set: {p['proved']} of {p['named']} named checks proved")
        return 0

    if a.check:
        base = read_baseline()
        if base is None:
            print(f"no mutation-coverage baseline at {os.path.relpath(BASELINE, ROOT)} — "
                  f"run: mutation_coverage.py --update", file=sys.stderr)
            return 1
        problems = []
        if c["proved"] < base["proved"]:
            problems.append(f"proved checks fell from {base['proved']} to {c['proved']}")
        if c["orphan_mutations"]:
            problems.append("mutation names no live check: "
                            + ", ".join(repr(o) for o in c["orphan_mutations"]))
        # A new check with no proof does not lower `proved`, so the count alone would not catch it.
        # The ratio does: adding an unproved check moves it down.
        was = base["proved"] / base["named"] if base["named"] else 0
        now = c["proved"] / c["named"] if c["named"] else 0
        if now < was - 1e-9:
            problems.append(
                f"coverage fell from {base['proved']}/{base['named']} ({was:.0%}) to "
                f"{c['proved']}/{c['named']} ({now:.0%}) — a new check arrived without a mutation")
        if problems:
            print("mutation coverage regressed:", file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            print("  prove the new check in tests/scripts/test_check_corpus.py, or move the "
                  "baseline deliberately with --update and say why in the commit", file=sys.stderr)
            return 1
        if not a.quiet:
            print(f"mutation coverage: {c['proved']}/{c['named']} named checks proved ({now:.0%})")
        return 0

    print(f"named checks:      {c['named']}")
    print(f"proved by mutation {c['proved']}  ({c['proved'] / c['named']:.0%})")
    print(f"mutation entries:  {c['mutations']}")
    if c["orphan_mutations"]:
        print("\nmutations naming no live check:")
        for o in c["orphan_mutations"]:
            print(f"  {o}")
    print("\nnot yet proved able to fail:")
    for n in c["unproved"]:
        print(f"  {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
