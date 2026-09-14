#!/usr/bin/env python3
"""Every throttled response in the published contract names the caller's budget (#96).

`docs/api/api-standards.md` §6 requires `X-RateLimit-Limit`, `X-RateLimit-Remaining` and
`Retry-After` on every throttled response. The corpus's own OpenAPI declared a 429 and carried none
of the three, so the contract it publishes was a step behind the standard it publishes.

This is not pedantry about headers. A caller that cannot read its own budget only discovers the
ceiling by hitting it, and without `Retry-After` it does not know when to come back, so it retries
at once — which is the load the limit exists to prevent. A rate limit without these headers turns a
well-behaved client into a source of the overload.

stdlib only: the corpus has no YAML parser, and the checks it needs here are textual anyway.

    check_rate_limit_contract.py            # report
    check_rate_limit_contract.py --check    # fail when a throttled response is missing one
"""
import argparse
import glob
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Contracts the corpus publishes itself. The adopting repository's own OpenAPI is its business;
# what this gate protects is what THIS repository hands to a reader as an example to follow.
CONTRACTS = ("docs/api/openapi/**/*.yaml", "specs/features/**/contracts/*.yaml")

REQUIRED = ("X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After")

# 429 only. The concurrency-backpressure 503 also carries a Retry-After per api-standards.md §6,
# and a first version of this check demanded it on every 503 — which fired on readiness responses
# ("Service not ready", "store unreachable") that owe no such header. Nothing in the text separates
# a saturation 503 from a readiness one without guessing, and a rule that guesses is the widening
# this corpus has rejected four times. So the backpressure path is left to review, said here rather
# than left as a silent gap.
_THROTTLED = re.compile(r'^(\s*)["\']?429["\']?\s*:', re.M)


def contracts():
    out = []
    for pattern in CONTRACTS:
        out += glob.glob(os.path.join(ROOT, pattern), recursive=True)
    return sorted(set(out))


def _response_block(text, match):
    """The lines of one response object: from its key to the next key at the same indent or less."""
    indent = len(match.group(1))
    rest = text[match.end():].split("\n")
    # The remainder of the matched line always belongs to the response. A flow-style entry puts the
    # whole object there — `"429": { description: …, headers: { … } }` — and a first version dropped
    # it, so every single-line response looked empty and reported all three headers missing.
    body = [rest[0]]
    for line in rest[1:]:
        if line.strip() and (len(line) - len(line.lstrip())) <= indent:
            break
        body.append(line)
    return "\n".join(body)


def problems():
    errs = []
    seen = 0
    for path in contracts():
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for m in _THROTTLED.finditer(text):
            seen += 1
            block = _response_block(text, m)
            missing = [h for h in REQUIRED if h not in block]
            if missing:
                line = text[:m.start()].count("\n") + 1
                errs.append(f"{rel}:{line} 429 response does not name {', '.join(missing)}")
    return errs, seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    errs, seen = problems()

    if not contracts():
        print("no published contract found to check", file=sys.stderr)
        return 1
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        print("  api-standards.md §6 requires these on every throttled response", file=sys.stderr)
        return 1
    if not a.quiet:
        print(f"throttled responses: {seen} checked, all name the caller's budget and Retry-After")
    return 0


if __name__ == "__main__":
    sys.exit(main())
