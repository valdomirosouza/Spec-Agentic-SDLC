#!/usr/bin/env python3
"""Adopting this corpus produces a repository that works — measured, not claimed (#108).

`adopt.sh` had three tests. They asserted that the JSON was well formed, that the file count was
right, and that `--force` behaved. None asked whether what landed was usable, which is why a
`governed` adoption could reach seventeen failures and two Python tracebacks without any gate
noticing: what was tested was that files were copied.

This adopts into a temporary directory and exercises the result, once per layer:

  links        every internal Markdown link in the adopted tree resolves (check_links.py)
  verifier     where the layer ships check-corpus.sh, it runs green and prints no traceback
  first run    the first command SETUP.md gives a newcomer creates a real feature bundle

The third is run for real rather than with --dry-run: a dry run never opens templates/, so it
would stay green in an adoption that copied none. The cost is printed on every run — three
adoptions of a 500-file corpus is not free, and the round-8 rule is that an expensive proof
declares its number rather than hiding it.

    check_adoption.py [--layer L]... [--check] [--quiet]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "python"))
import check_links                                                       # noqa: E402
LAYERS = ("minimal", "governed", "full")
FEATURE = "Add cursor pagination to the requests list"


def run(cmd, cwd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)


def adopt(layer, target):
    r = run(["bash", os.path.join(ROOT, "scripts", "bash", "adopt.sh"), target,
             "--layer", layer, "--json"], ROOT)
    if r.returncode != 0:
        return f"adopt.sh --layer {layer} exited {r.returncode}: {r.stderr.strip()[:200]}"
    return None


def check_layer(layer):
    """[] when a fresh adoption of this layer works; one string per way it does not."""
    target = tempfile.mkdtemp(prefix=f"adoption-{layer}-")
    try:
        err = adopt(layer, target)
        if err:
            return [err]
        problems = []

        # A repository, because the corpus's scripts locate themselves from the git root.
        run(["git", "init", "-q"], target)
        run(["git", "config", "user.email", "adoption-check@example.invalid"], target)
        run(["git", "config", "user.name", "adoption check"], target)

        _, bad = check_links.broken_links(target)
        if bad:
            problems.append(f"{layer}: {len(bad)} broken link(s) in the adopted tree, "
                            f"first: {bad[0]}")

        # A corpus made to be copied normalises line endings wherever it lands, or a contributor
        # on another platform produces a diff that touches whole files and the link and frontmatter
        # checks read content an editor rewrote (#109).
        for name in (".gitattributes", ".editorconfig"):
            if not os.path.exists(os.path.join(target, name)):
                problems.append(f"{layer}: {name} did not arrive — the adopted tree has no "
                                f"line-ending normalisation")

        verifier = os.path.join(target, "scripts", "bash", "check-corpus.sh")
        if os.path.exists(verifier):
            v = run(["bash", verifier, "--no-smoke", "--no-suites"], target)
            out = v.stdout + v.stderr
            if "Traceback" in out:
                line = next((l for l in out.split("\n") if "Error" in l), "Traceback")
                problems.append(f"{layer}: the verifier raised in a fresh adoption — {line.strip()[:120]}")
            if v.returncode != 0:
                failed = [l.strip() for l in out.split("\n") if l.lstrip().startswith("✗")]
                problems.append(f"{layer}: the verifier reported {v.returncode} failure(s) a new "
                                f"adopter cannot act on — {'; '.join(failed[:3])}")

        first = run(["bash", os.path.join(target, "scripts", "bash", "create-new-feature.sh"),
                     "--json", FEATURE], target)
        if first.returncode != 0:
            problems.append(f"{layer}: the first command in SETUP.md exited {first.returncode}: "
                            f"{(first.stderr or first.stdout).strip()[:160]}")
        else:
            try:
                d = json.loads(first.stdout.strip().split("\n")[-1])
                spec = d["SPEC_FILE"]
                size = os.path.getsize(spec)
                if size < 500:
                    problems.append(f"{layer}: the first command produced a {size}-byte spec — "
                                    f"the template did not arrive")
            except (ValueError, KeyError, OSError) as e:
                problems.append(f"{layer}: the first command answered something unusable: {e}")
        return problems
    finally:
        shutil.rmtree(target, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--layer", choices=LAYERS, action="append")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    t0 = time.time()
    problems = []
    for layer in (a.layer or list(LAYERS)):
        p = check_layer(layer)
        problems += p
        if not a.quiet:
            print(f"{layer}: {'adopts clean' if not p else chr(10).join(p)}")
    secs = int(time.time() - t0)
    if not a.quiet:
        print(f"{len(a.layer or LAYERS)} layer(s) adopted and exercised · {secs}s wall clock")
    if problems and a.check:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    if a.check:
        print(f"adoption works in {len(a.layer or LAYERS)} layer(s) · {secs}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
