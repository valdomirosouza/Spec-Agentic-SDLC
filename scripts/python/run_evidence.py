#!/usr/bin/env python3
"""IPE evidence for a batch run: step manifests and a hash-chained ledger (ADR-0102). stdlib only.

A step that produces data writes a manifest beside its output: the run ID and commit (ADR-0101),
its inputs (source, the query path and its SHA-256 at that commit, the parameters, the extraction
time) and its outputs (path, SHA-256, row count, a hash of the column list). A manifest holds
metadata only, never data values. Shape: docs/audit/schema/step-manifest.schema.json.

Each file copied to write-once storage appends one line to the run's ledger: its sequence number,
the run ID, the step, the path, the file's SHA-256, and `prev`, the SHA-256 of the previous line's
exact bytes (64 zeros for the first). Deleting, editing or reordering a line breaks the chain from
there on. Shape: docs/audit/schema/evidence-ledger.schema.json. A chain proves nothing on its own
if the whole ledger can be rewritten, and an edit to the last line breaks no later link. So the
ledger is copied write-once when the run ends (for a run with a reconciliation `break` or
`not_run`, once its exceptions are recorded, ADR-0103 §4), and its head (the SHA-256 of its last line) is kept
with the copy: `verify --expect-head` compares against it.

Python:

    import run_evidence as ev
    m = ev.manifest(run.run_id, run.commit, "extract",
                    inputs=[ev.source("erp", repo=".", commit=run.commit,
                                      query_path="sql/receivables.sql",
                                      parameters={"period": "2026-10"})],
                    outputs=[ev.output("out/receivables.csv", rows=1200,
                                       columns=["invoice", "due", "amount"])])
    ev.write_manifest("out/receivables.manifest.json", m)
    ev.append("evidence/ledger.jsonl", run.run_id, "extract", "out/receivables.csv")

Verify:

    run_evidence.py verify evidence/ledger.jsonl [--root DIR] [--expect-head HEX]
        # the chain; with --root, each file's hash; with --expect-head, the sealed head
    run_evidence.py check-manifest out/receivables.manifest.json
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

import reconcile as rc

ZERO = "0" * 64
HEX = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ISO = "%Y-%m-%dT%H:%M:%SZ"
# ADR-0102 §5: until retention above the classification cap has a decided route, a write-once copy
# holds non-personal data or a pseudonymised extract. When the file cannot be kept, its hash is.
COPIES = ("full", "pseudonymised", "hash_only")
LEDGER_FIELDS = ("seq", "run_id", "step", "path", "sha256", "prev")
MANIFEST_FIELDS = ("run_id", "commit", "step", "inputs", "outputs")
INPUT_FIELDS = ("source", "query_path", "query_sha256", "parameters", "extracted_at")
OUTPUT_FIELDS = ("path", "sha256", "rows", "columns_sha256", "copy")
# ADR-0103 §2: the verdicts of the reconciliations the step judged, when it judged any.
OPTIONAL_FIELDS = ("reconciliations",)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def columns_sha256(columns):
    """A hash of the column list, in order: a renamed, added or reordered column changes it."""
    return hashlib.sha256("\n".join(columns).encode("utf-8")).hexdigest()


def query_sha256(repo, commit, path):
    """The query's SHA-256 as committed, not as it sits in the working tree."""
    r = subprocess.run(["git", "-C", repo, "show", f"{commit}:{path}"], capture_output=True)
    if r.returncode != 0:
        raise ValueError(f"{path} is not in commit {commit[:12]}")
    return hashlib.sha256(r.stdout).hexdigest()


def source(name, repo=".", commit=None, query_path=None, parameters=None, extracted_at=None):
    return {"source": name, "query_path": query_path,
            "query_sha256": query_sha256(repo, commit, query_path) if query_path else None,
            "parameters": parameters or {},
            "extracted_at": extracted_at or datetime.datetime.now(datetime.timezone.utc).strftime(ISO)}


def output(path, rows=None, columns=None, copy="full"):
    return {"path": path, "sha256": sha256_file(path), "rows": rows,
            "columns_sha256": columns_sha256(columns) if columns is not None else None, "copy": copy}


def manifest(run_id, commit, step, inputs, outputs, reconciliations=None):
    m = {"run_id": run_id, "commit": commit, "step": step, "inputs": inputs, "outputs": outputs}
    if reconciliations is not None:
        m["reconciliations"] = reconciliations
    problems = manifest_problems(m)
    if problems:
        raise ValueError("; ".join(problems))
    return m


def write_manifest(path, m):
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(m, indent=2, sort_keys=True) + "\n")


def _last_line(ledger):
    if not os.path.exists(ledger):
        return None
    last = None
    with open(ledger, "rb") as f:
        for line in f:
            if line.strip():
                last = line.rstrip(b"\n")
    return last


def append(ledger, run_id, step, path, sha256=None):
    """Append one entry for a file copied write-once. Returns the entry."""
    last = _last_line(ledger)
    seq = json.loads(last)["seq"] + 1 if last else 1
    entry = {"seq": seq, "run_id": run_id, "step": step, "path": path,
             "sha256": sha256 or sha256_file(path),
             "prev": hashlib.sha256(last).hexdigest() if last else ZERO}
    os.makedirs(os.path.dirname(os.path.abspath(ledger)), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return entry


def head(ledger):
    """The SHA-256 of the ledger's last line: what seals it."""
    last = _last_line(ledger)
    return hashlib.sha256(last).hexdigest() if last else None


def ledger_problems(ledger, root=None, expect_head=None):
    """Recompute the chain; with `root`, also check each file's hash under it."""
    out, prev_bytes, run_ids, n = [], None, set(), 0
    with open(ledger, "rb") as f:
        lines = [l.rstrip(b"\n") for l in f if l.strip()]
    if not lines:
        return ["the ledger is empty"]
    for i, raw in enumerate(lines, 1):
        try:
            e = json.loads(raw)
        except ValueError:
            out.append(f"line {i}: not JSON")
            prev_bytes = raw
            continue
        if not isinstance(e, dict) or set(e) != set(LEDGER_FIELDS):
            out.append(f"line {i}: must have exactly {', '.join(LEDGER_FIELDS)}")
            prev_bytes = raw
            continue
        n += 1
        expected = hashlib.sha256(prev_bytes).hexdigest() if prev_bytes is not None else ZERO
        if e["prev"] != expected:
            out.append(f"line {i}: chain broken — prev does not match the line before it")
        if e["seq"] != i:
            out.append(f"line {i}: seq {e['seq']} out of order")
        if not isinstance(e["sha256"], str) or not HEX.match(e["sha256"]):
            out.append(f"line {i}: sha256 is not a SHA-256")
        run_ids.add(e["run_id"])
        if root is not None and isinstance(e["path"], str):
            p = os.path.join(root, e["path"])
            if not os.path.isfile(p):
                out.append(f"line {i}: {e['path']} is missing under {root}")
            elif sha256_file(p) != e["sha256"]:
                out.append(f"line {i}: {e['path']} does not match its recorded hash")
        prev_bytes = raw
    if expect_head is not None and hashlib.sha256(lines[-1]).hexdigest() != expect_head:
        out.append("the head does not match the sealed one: the last line changed, or lines were added or removed at the end")
    if len(run_ids) > 1:
        out.append(f"the ledger mixes runs: {', '.join(sorted(map(str, run_ids)))}")
    return out


def manifest_problems(m):
    if not isinstance(m, dict):
        return ["not a JSON object"]
    out = [f"missing {k}" for k in MANIFEST_FIELDS if k not in m]
    if out:
        return out
    out += [f"unknown field {k}" for k in m if k not in MANIFEST_FIELDS + OPTIONAL_FIELDS]
    verdicts = m.get("reconciliations")
    if "reconciliations" in m:
        if not isinstance(verdicts, list) or not verdicts:
            out.append("reconciliations must be a non-empty list")
            verdicts = None
        else:
            for v in verdicts:
                out += rc.verdict_problems(v)
                if isinstance(v, dict) and v.get("step") != m["step"]:
                    out.append(f"{v.get('id')}: a verdict in this manifest was judged by another step")
    if not isinstance(m["commit"], str) or not SHA_RE.match(m["commit"]):
        out.append("commit is not a full 40-character SHA")
    for kind, fields, items in (("input", INPUT_FIELDS, m["inputs"]), ("output", OUTPUT_FIELDS, m["outputs"])):
        if kind == "output" and verdicts and items == []:
            continue  # a step that only reconciles produces no data
        if not isinstance(items, list) or not items:
            out.append(f"{kind}s must be a non-empty list")
            continue
        for i, it in enumerate(items):
            if not isinstance(it, dict) or set(it) != set(fields):
                out.append(f"{kind} {i} must have exactly {', '.join(fields)}")
                continue
            if kind == "input":
                if (it["query_path"] is None) != (it["query_sha256"] is None):
                    out.append(f"input {i}: a query path needs its hash at the commit, and only then")
                if it["query_sha256"] is not None and not HEX.match(str(it["query_sha256"])):
                    out.append(f"input {i}: query_sha256 is not a SHA-256")
                if not isinstance(it["parameters"], dict) or any(
                        isinstance(v, (dict, list)) for v in it["parameters"].values()):
                    out.append(f"input {i}: parameters must be a flat object of scalars")
            else:
                if not HEX.match(str(it["sha256"])):
                    out.append(f"output {i}: sha256 is not a SHA-256")
                if it["copy"] not in COPIES:
                    out.append(f"output {i}: copy {it['copy']!r} is not one of {', '.join(COPIES)}")
                if it["rows"] is not None and (not isinstance(it["rows"], int) or isinstance(it["rows"], bool)
                                               or it["rows"] < 0):
                    out.append(f"output {i}: rows is not a non-negative integer or null")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="recompute a ledger's chain")
    v.add_argument("ledger")
    v.add_argument("--root", help="also check each file's hash under this directory")
    v.add_argument("--expect-head", help="the head kept with the write-once copy of the ledger")
    c = sub.add_parser("check-manifest", help="validate a step manifest")
    c.add_argument("manifest")
    a = ap.parse_args(argv)
    if a.cmd == "verify":
        problems, name = ledger_problems(a.ledger, a.root, a.expect_head), a.ledger
        if not problems:
            print(f"head {head(a.ledger)}")
    else:
        try:
            with open(a.manifest, encoding="utf-8") as f:
                problems = manifest_problems(json.load(f))
        except ValueError as e:
            problems = [f"not JSON ({e})"]
        name = a.manifest
    for p in problems:
        print(p)
    print(f"{name}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
