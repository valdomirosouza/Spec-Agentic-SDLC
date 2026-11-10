<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Audit package for a sampled run — builder template (ADR-0102)

When an auditor samples a run of a `batch-data` pipeline, the answer is one package, built from
**the commit that ran**, never from the working tree. Building it twice for the same run gives the
same content, checked by its `SHA256SUMS`.

## What the run leaves behind

A run wrapped by `scripts/python/run_record.py` (ADR-0101) appends its record to the run history.
Each data-producing step writes a manifest, and each file it copies to write-once storage appends
a line to the run's ledger (`scripts/python/run_evidence.py`). When the run ends, failed runs
included, the run's directory in the write-once store is sealed:

```text
<store>/<run-id>/
  ledger.jsonl                    # one line per copied file, hash-chained
  ledger.head                     # SHA-256 of the ledger's last line, written when the run ends
  manifests/<step>.manifest.json  # one per data-producing step
  copies/…                        # the outputs; paths in the ledger are relative to <run-id>/
```

Write-once means a retention lock in compliance mode, or an equivalent you declare. A shared
drive or an ordinary git repository is not write-once. Until retention above the classification
cap has a decided route, `copies/` holds non-personal data or a pseudonymised extract only. Each
output's `copy` field in its manifest says which, and `hash_only` means only the hash was kept
(ADR-0102 §5).

## Builder

Copy this script into the adopting repository, for example to `scripts/bash/build-audit-package.sh`.
It reads the store and never writes to it.

```sh
#!/bin/sh
# build-audit-package.sh <run-id> <run-history.jsonl> <store>/<run-id> <out-dir>
set -eu
RUN=$1 HISTORY=$2 SEALED=$3 OUT=$4
PKG="$OUT/$RUN"
[ ! -e "$PKG" ] || { echo "refusing: $PKG exists; a package is built once into a new directory" >&2; exit 1; }

# 1. The run record, and from it the commit that ran.
grep -F "\"run_id\": \"$RUN\"" "$HISTORY" > /dev/null || { echo "no record for $RUN" >&2; exit 1; }
mkdir -p "$PKG"
grep -F "\"run_id\": \"$RUN\"" "$HISTORY" > "$PKG/run-record.json"
COMMIT=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["commit"])' < "$PKG/run-record.json")

# 2. The code and queries at that commit.
mkdir "$PKG/code"
git archive --format=tar "$COMMIT" | tar -x -C "$PKG/code"

# 3. The sealed evidence, as it is in the store.
cp -R "$SEALED/ledger.jsonl" "$SEALED/ledger.head" "$SEALED/manifests" "$SEALED/copies" "$PKG/"

# 4. Verification: the chain, the sealed head, every copy against its hash, every manifest.
#    Every check runs and is reported; any one failing fails the build.
( cd "$PKG"
  failed=0
  python3 code/scripts/python/run_evidence.py verify ledger.jsonl --root . --expect-head "$(cat ledger.head)" \
      > verification.txt 2>&1 || failed=1
  for m in manifests/*.manifest.json; do
      python3 code/scripts/python/run_evidence.py check-manifest "$m" >> verification.txt 2>&1 || failed=1
  done
  if [ "$failed" -ne 0 ]; then
      cat verification.txt
      echo "verification failed: the package is not evidence" >&2
      exit 1
  fi
  find . -type f ! -name SHA256SUMS | LC_ALL=C sort | xargs shasum -a 256 > SHA256SUMS )
echo "$PKG"
```

The verifier runs from `code/`, the copy at the run's commit. That copy has to include
`scripts/python/run_evidence.py`. A commit from before the evidence tooling was adopted cannot
produce a package, and that is itself a finding.

## The package

| Path                          | Answers                                                                        |
| ----------------------------- | ------------------------------------------------------------------------------ |
| `run-record.json`             | which run, from which commit, by whom, with what outcome (ADR-0101)            |
| `code/`                       | the queries and scripts exactly as they ran (`git archive <commit>`)           |
| `manifests/`                  | each step's inputs, parameters and query hash, and each output's hash and rows |
| `ledger.jsonl`, `ledger.head` | what was copied write-once, in order, and that nothing changed since           |
| `copies/`                     | the outputs (or pseudonymised extracts) the report relied on                   |
| `verification.txt`            | the verifier's result over all of the above                                    |
| `SHA256SUMS`                  | the package's own content, so a second build can be compared with the first    |

To check reproducibility, build the package again into another directory and compare the two
`SHA256SUMS` files. They are equal when the run, its commit and the sealed store are unchanged.
