#!/usr/bin/env python3
"""Files this repository refuses to distribute stay undistributed (R15-T2).

`ARCHITECTURE.md` and `.corpus-origin` describe the corpus, not the product that adopts it. They
were out of all three layers — by the accident of not appearing in an include list. Nothing
asserted it, and the `full` layer's list already names `README.md`, `CONTRIBUTING.md` and
`CITATION.cff`, so adding `ARCHITECTURE.md` beside them is a plausible edit that no gate would
have questioned. An adopter would then inherit a description of somebody else's repository.

The exclusion is now declared in `adopt.sh` (`NEVER_ADOPTED`) and asserted here, against what
`adopt.sh --list` actually produces rather than against the list it was told to produce.

    check_layer_exclusions.py [--check] [--quiet]
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ADOPT = os.path.join(ROOT, "scripts", "bash", "adopt.sh")
LAYERS = ("minimal", "governed", "full")


def never_adopted():
    """The declaration, read out of adopt.sh rather than restated here."""
    with open(ADOPT, encoding="utf-8") as fh:
        m = re.search(r'^NEVER_ADOPTED="([^"]*)"', fh.read(), re.M)
    return m.group(1).split() if m else []


def leaked():
    """[(layer, file)] for every declared exclusion that a layer would copy anyway."""
    declared = never_adopted()
    if not declared:
        return None, "adopt.sh declares no NEVER_ADOPTED: the exclusion is prose again"
    out = []
    for layer in LAYERS:
        r = subprocess.run(["bash", ADOPT, "--list", "--layer", layer, "/tmp/__exclusion_probe"],
                           capture_output=True, text=True, cwd=ROOT, timeout=300)
        if r.returncode != 0:
            return None, f"adopt.sh --list --layer {layer} exited {r.returncode}"
        files = {l.strip() for l in r.stdout.split("\n") if l.strip()}
        out += [(layer, f) for f in declared if f in files]
    return out, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    bad, err = leaked()
    if err:
        print(err, file=sys.stderr)
        return 1
    declared = never_adopted()
    # A declaration naming a file that does not exist is a rule guarding nothing.
    ghosts = [f for f in declared if not os.path.exists(os.path.join(ROOT, f))]
    if not a.quiet:
        if bad or ghosts:
            for layer, f in bad:
                print(f"{f} is declared never-adopted and the {layer} layer copies it")
            for f in ghosts:
                print(f"{f} is declared never-adopted but does not exist")
        else:
            print(f"{len(declared)} declared exclusion(s) absent from all {len(LAYERS)} layers")
    if a.check and (bad or ghosts):
        for layer, f in bad:
            print(f"{f}: the {layer} layer copies a file this repository refuses to distribute",
                  file=sys.stderr)
        for f in ghosts:
            print(f"{f}: declared never-adopted but absent from the repository", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
