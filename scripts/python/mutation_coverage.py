#!/usr/bin/env python3
"""How much of check-corpus.sh has been proved able to fail, and a ratchet on that number (#75).

The mutation harness answers "can this check fail when fed its own defect". It answered that for
14 of 46 named checks and nothing asked about the other 32, so anyone could add check 47 with no
proof at all and the build would stay green. That is the round-5 finding one level up: the
verifier became partly verified, and the verification of the verifier had no guard.

The shape is borrowed from the corpus's own test-integrity gate (ADR-0065): a versioned baseline,
a failure when the number falls, and a deliberate, visible act to move it. It does not demand
46 of 46 today. It demands that the number never quietly go down.

Guarding the ratio alone was not enough, and the way it failed is worth stating: a ratio rises
when its denominator shrinks, so deleting twenty unproved checks moved coverage from 32% to 52%
and the gate approved it. A gate built to protect verification had made removing verification the
cheapest way to satisfy the gate. Mutation testing could not find that — the ratchet passed every
one of its own tests, because proving a gate can FAIL says nothing about what it REWARDS when it
passes (#79). The baseline records the check names now, and losing one is a failure.

    mutation_coverage.py            # report coverage and list what is unproved
    mutation_coverage.py --check    # fail if coverage fell, or if a check went missing
    mutation_coverage.py --update   # record the current names and numbers as the new baseline
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
# The status token that follows the name. `;` may be glued on by `{ result X fail; ... }`.
_RESULT_STATUS = re.compile(r'\bresult\s+"([^"]+)"\s+(ok|note|fail)\b')


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


def call_sites():
    """Every check name mapped to the set of statuses it can print."""
    with open(VERIFIER, encoding="utf-8") as fh:
        text = fh.read()
    sites = {}
    for name, status in _RESULT_STATUS.findall(text):
        sites.setdefault(name, set()).add(status)
    # A name whose status is not a literal token cannot be classified here; say so rather than
    # counting it as fine.
    for name in _RESULT.findall(text):
        sites.setdefault(name, set())
    return sites


def vacuity_problems():
    """A check name that can only ever print `ok` is vacuous by construction.

    Neutering a check — replacing its two-branch construct with an unconditional pass — keeps the
    name, so the coverage ratchet, which guards names, approves it. Proved by doing exactly that:
    the verifier printed `✓ bash -n — neutered` and the build stayed green (R8-T1).

    What this does NOT catch, stated here so it does not become a later round's finding: a
    condition that is always true. `if true; then result X ok; else result X fail; fi` has both
    sites and is just as vacuous. Mutation coverage is the deeper guard; this is the cheap one,
    it costs no runtime at all, and it covers the shape that was actually exploitable."""
    problems = []
    for name, statuses in sorted(call_sites().items()):
        if not statuses:
            problems.append(f"`{name}` has no literal status token, so it cannot be classified")
        elif "fail" not in statuses:
            problems.append(f"`{name}` can only print {'/'.join(sorted(statuses))} — it has no "
                            f"failing path, so nothing it checks can ever fail the build")
    return problems


def coverage():
    """Which named checks a mutation covers.

    A harness entry names a check by the same substring the harness matches against the failure
    line, so the mapping here has to use that same rule — anything stricter would report checks as
    unproved that the harness does in fact prove."""
    names, proofs = named_checks(), proved_names()
    covered, orphan, ambiguous = set(), [], []
    for p in proofs:
        # An exact name is unambiguous by definition and wins outright; otherwise the proof must
        # match exactly one check. A bare substring let one proof count for two checks —
        # `check_control_matrix` also matched `tests/scripts/test_check_control_matrix.py` — so the
        # number was inflated by proofs that cannot say which check they proved (R9-T1). Anchoring
        # at the start instead was too strict and dropped legitimate mid-name proofs; both wrong
        # answers were measured before this one was kept.
        hits = [p] if p in names else [n for n in names if p in n]
        if len(hits) == 1:
            covered.update(hits)
        elif not hits:
            orphan.append(p)
        else:
            ambiguous.append((p, hits))
    return {
        "named": len(names),
        "proved": len(covered),
        "mutations": len(proofs),
        "unproved": sorted(set(names) - covered),
        "orphan_mutations": orphan,
        "ambiguous_mutations": ambiguous,
    }


def read_baseline():
    if not os.path.isfile(BASELINE):
        return None
    with open(BASELINE, encoding="utf-8") as fh:
        return json.load(fh)


def write_baseline(c):
    payload = {
        "_comment": "Mutation coverage ratchet (#75, #79). Raise it by proving more checks. Lowering "
                    "it — including by deleting checks — is a deliberate act that belongs in a "
                    "commit message, not a side effect.",
        "named": c["named"],
        "proved": c["proved"],
        # The names, not just the count. Without them the ratio was the only guard, and a ratio
        # goes UP when the denominator shrinks: deleting twenty unproved checks moved coverage
        # from 32% to 52% and passed (#79). Recording the set lets the failure say which check
        # went missing rather than that a number changed.
        "checks": named_checks(),
    }
    with open(BASELINE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return payload


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if coverage fell below the baseline")
    ap.add_argument("--update", action="store_true", help="record current coverage as the baseline")
    ap.add_argument("--vacuity", action="store_true",
                    help="fail if any check name has no failing path")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    c = coverage()

    if a.vacuity:
        problems = vacuity_problems()
        if problems:
            print("check(s) that cannot fail:", file=sys.stderr)
            for p in problems:
                print(f"  {p}", file=sys.stderr)
            return 1
        if not a.quiet:
            print(f"every one of the {c['named']} named checks has a failing path")
        return 0

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
        # The denominator is guarded first, because the ratio cannot guard it: removing an unproved
        # check raises coverage. A gate built to protect verification made deleting it the cheapest
        # way to satisfy the gate (#79).
        gone = sorted(set(base.get("checks", [])) - set(named_checks()))
        if gone:
            problems.append(f"{len(gone)} check(s) the baseline knows about are no longer in "
                            f"check-corpus.sh:")
            problems.extend(f"    {g}" for g in gone)
        if c["proved"] < base["proved"]:
            problems.append(f"proved checks fell from {base['proved']} to {c['proved']}")
        if c["orphan_mutations"]:
            problems.append("mutation names no live check: "
                            + ", ".join(repr(o) for o in c["orphan_mutations"]))
        for name, hits in c.get("ambiguous_mutations", []):
            problems.append(f"mutation {name!r} matches {len(hits)} checks and so cannot say which "
                            f"it proved: {hits}")
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
