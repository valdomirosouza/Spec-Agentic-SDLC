#!/usr/bin/env python3
"""The record of a batch run, written even when the run fails (ADR-0101). stdlib only.

A run gets an ID at its start, `<pipeline>-<UTC YYYYMMDDTHHMMSSZ>`, and the commit it executes and
whether the working tree was clean are recorded before the first step. A production run from a
dirty tree is refused. Whatever the outcome, one JSON line is appended to the run history; the
line's shape is docs/sre/slo/schema/run-record.schema.json. A rerun is a new run with a new ID.

Python — wrap the run and each step:

    from run_record import Run
    with Run("o2c", history="runs/history.jsonl", production=True) as run:
        with run.step("extract") as step:
            rows = extract()
            step.count(rows_in=len(rows), rows_out=len(rows), rows_rejected=0)

Shell — let this script run the steps, in order, stopping at the first that fails:

    run_record.py exec --pipeline o2c --history runs/history.jsonl --production \\
        --step extract="./extract.sh --period 2026-10" --step load=./load.sh

  Each step runs without a shell and sees RUN_ID and RUN_STEP_COUNTS in its environment. It may
  write `rows_in=N`, `rows_out=N` and `rows_rejected=N` lines to the RUN_STEP_COUNTS file.

A pipeline that declares reconciliations (ADR-0103) passes them to the run, `reconciliations=` in
Python or `--reconciliations FILE` to exec. The record then holds one verdict per declaration
(scripts/python/reconcile.py), and a `break` or `not_run` fails the step that judged it. A shell
step writes what it measured to RUN_RECONCILIATIONS, one `id=source,target` line each.

Check a history:

    run_record.py check runs/history.jsonl     # exit 1 on a malformed or inconsistent line

The record holds counts and identifiers, never data values.
"""
import argparse
import datetime
import getpass
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time

import reconcile as rc

RUN_STATUSES = ("succeeded", "failed", "aborted")
STEP_STATUSES = ("succeeded", "failed", "aborted")
COUNTS = ("rows_in", "rows_out", "rows_rejected")
FIELDS = ("run_id", "pipeline", "commit", "dirty", "production", "operator", "started_at",
          "ended_at", "status", "steps")
# ADR-0103 §2: present when the pipeline declares reconciliations, one verdict per declaration.
OPTIONAL_FIELDS = ("reconciliations",)
STEP_FIELDS = ("name", "status", "duration_seconds") + COUNTS
PIPELINE_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
STAMP = "%Y%m%dT%H%M%SZ"
ISO = "%Y-%m-%dT%H:%M:%SZ"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class RunRefused(Exception):
    """The run cannot start: no commit to record, or a production run from a dirty tree."""


def _git(repo, *args):
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        raise RunRefused(f"git {' '.join(args)} failed in {repo}: {r.stderr.strip()[:120]}")
    return r.stdout


class Step:
    def __init__(self, run, name):
        self.run, self.name = run, name
        self.counts = dict.fromkeys(COUNTS)

    def count(self, rows_in=None, rows_out=None, rows_rejected=None):
        for k, v in (("rows_in", rows_in), ("rows_out", rows_out), ("rows_rejected", rows_rejected)):
            if v is not None:
                if not isinstance(v, int) or isinstance(v, bool) or v < 0:
                    raise ValueError(f"{k} must be a non-negative integer, got {v!r}")
                self.counts[k] = v

    def reconcile(self, measured):
        """Judge the declared reconciliations this step measured; `measured` maps an ID to its
        (source, target). A `break` or `not_run` fails the step (ADR-0103 §3)."""
        if self.run.declared is None:
            raise ValueError("the run was started without reconciliations to judge")
        done = {v["id"] for v in self.run.reconciliations}
        again = sorted(done & set(measured))
        if again:
            raise ValueError(f"already judged in this run: {', '.join(again)}")
        verdicts = [v for v in rc.check(self.run.declared, measured, step=self.name) if v["id"] in measured]
        self.run.reconciliations += verdicts
        failing = [f"{v['id']} {v['verdict']}" for v in verdicts if v["verdict"] in rc.FAILING]
        if failing:
            raise rc.ReconciliationFailed(", ".join(failing))
        return verdicts

    def __enter__(self):
        self.t0 = time.monotonic()
        return self

    def __exit__(self, exc_type, exc, tb):
        status = ("succeeded" if exc_type is None
                  else "failed" if issubclass(exc_type, Exception) else "aborted")
        self.run.steps.append({"name": self.name, "status": status,
                               "duration_seconds": round(time.monotonic() - self.t0, 3),
                               **self.counts})
        return False


class Run:
    """One run of a pipeline. The record is appended on exit, whatever the outcome."""

    def __init__(self, pipeline, history, production=False, repo=".", operator=None, now=None,
                 reconciliations=None):
        if not PIPELINE_RE.match(pipeline):
            raise ValueError(f"pipeline {pipeline!r} must match {PIPELINE_RE.pattern}")
        self.pipeline, self.history, self.production, self.repo = pipeline, history, production, repo
        self.operator = operator or os.environ.get("RUN_OPERATOR") or getpass.getuser()
        self._now = now or (lambda: datetime.datetime.now(datetime.timezone.utc))
        self.steps = []
        self.declared, self.reconciliations = reconciliations, []

    def step(self, name):
        return Step(self, name)

    def __enter__(self):
        start = self._now()
        self.started_at = start.strftime(ISO)
        self.run_id = f"{self.pipeline}-{start.strftime(STAMP)}"
        # Before the first step (§1). With no commit there is nothing to tie the run to.
        self.commit = _git(self.repo, "rev-parse", "HEAD").strip()
        self.dirty = bool(_git(self.repo, "status", "--porcelain").strip())
        if self.production and self.dirty:
            # Refused, and the refusal is itself recorded: a run that never started is still a run
            # someone attempted.
            self._append("aborted")
            raise RunRefused(f"{self.run_id}: a production run needs a clean working tree")
        return self

    def __exit__(self, exc_type, exc, tb):
        status = ("succeeded" if exc_type is None
                  else "failed" if issubclass(exc_type, Exception) else "aborted")
        self._append(status)
        return False

    def record(self, status):
        extra = {}
        if self.declared is not None:
            # A declared reconciliation the run never reached is not_run: one verdict each.
            done = {v["id"] for v in self.reconciliations}
            extra["reconciliations"] = self.reconciliations + [
                v for v in rc.check(self.declared, {}) if v["id"] not in done]
            if status == "succeeded" and any(v["verdict"] in rc.FAILING for v in extra["reconciliations"]):
                status = "failed"
        return {**extra, "run_id": self.run_id, "pipeline": self.pipeline, "commit": self.commit,
                "dirty": self.dirty, "production": self.production, "operator": self.operator,
                "started_at": self.started_at, "ended_at": self._now().strftime(ISO),
                "status": status, "steps": self.steps}

    def _append(self, status):
        os.makedirs(os.path.dirname(os.path.abspath(self.history)), exist_ok=True)
        with open(self.history, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.record(status), sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


def read_counts(path):
    counts = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            k, _, v = line.strip().partition("=")
            if k in COUNTS and v.strip().isdigit():
                counts[k] = int(v)
    return counts


def execute(pipeline, history, steps, production=False, repo=".", reconciliations=None):
    """Run `steps` [(name, command)] in order inside one Run. Returns the exit code.

    With `reconciliations` (a declarations file), a step may write what it measured to the
    RUN_RECONCILIATIONS file, one `id=source,target[,one_side]` line per reconciliation.
    """
    try:
        declared = rc.load(reconciliations) if reconciliations else None
        with Run(pipeline, history, production=production, repo=repo, reconciliations=declared) as run:
            print(run.run_id, flush=True)
            for name, command in steps:
                paths = []
                for kind in ("counts", "reconciliations"):
                    fd, p = tempfile.mkstemp(prefix=f"{run.run_id}-{name}-{kind}-")
                    os.close(fd)
                    paths.append(p)
                counts_path, measured_path = paths
                try:
                    env = dict(os.environ, RUN_ID=run.run_id, RUN_STEP_COUNTS=counts_path,
                               RUN_RECONCILIATIONS=measured_path)
                    with run.step(name) as step:
                        code = subprocess.run(shlex.split(command), cwd=repo, env=env).returncode
                        step.count(**read_counts(counts_path))
                        if code != 0:
                            raise RuntimeError(f"step {name} exited {code}")
                        measured = rc.read_measured(measured_path)
                        if measured:
                            step.reconcile(measured)
                finally:
                    for p in paths:
                        os.unlink(p)
    except RunRefused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except (RuntimeError, OSError, ValueError, rc.ReconciliationFailed) as e:
        print(f"failed: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("aborted", file=sys.stderr)
        return 130
    return 0


def _time(s):
    return datetime.datetime.strptime(s, ISO) if isinstance(s, str) else None


def line_problems(rec):
    """What is wrong with one record. An empty list means the record is well formed."""
    if not isinstance(rec, dict):
        return ["not a JSON object"]
    out = [f"missing {k}" for k in FIELDS if k not in rec]
    if out:
        return out
    out += [f"unknown field {k}" for k in rec if k not in FIELDS + OPTIONAL_FIELDS]
    if not isinstance(rec["pipeline"], str) or not PIPELINE_RE.match(rec["pipeline"]):
        out.append(f"pipeline {rec['pipeline']!r} is not a valid name")
    if not isinstance(rec["commit"], str) or not SHA_RE.match(rec["commit"]):
        out.append("commit is not a full 40-character SHA")
    for k in ("dirty", "production"):
        if not isinstance(rec[k], bool):
            out.append(f"{k} is not a boolean")
    if not isinstance(rec["operator"], str) or not rec["operator"]:
        out.append("operator is empty")
    try:
        start, end = _time(rec["started_at"]), _time(rec["ended_at"])
    except ValueError:
        start = end = None
    if start is None or end is None:
        out.append(f"started_at and ended_at must be UTC {ISO}")
    else:
        if end < start:
            out.append("ended_at is before started_at")
        if rec["run_id"] != f"{rec['pipeline']}-{start.strftime(STAMP)}":
            out.append("run_id is not <pipeline>-<started_at as YYYYMMDDTHHMMSSZ>")
    if rec["status"] not in RUN_STATUSES:
        out.append(f"status {rec['status']!r} is not one of {', '.join(RUN_STATUSES)}")
    if rec["production"] is True and rec["dirty"] is True and rec["status"] != "aborted":
        out.append("a production run from a dirty tree ran instead of being refused")
    steps = rec["steps"] if isinstance(rec["steps"], list) else None
    if steps is None:
        return out + ["steps is not a list"]
    for i, s in enumerate(steps):
        if not isinstance(s, dict) or set(s) != set(STEP_FIELDS):
            out.append(f"step {i} must have exactly {', '.join(STEP_FIELDS)}")
            continue
        if s["status"] not in STEP_STATUSES:
            out.append(f"step {s['name']!r} status {s['status']!r} is unknown")
        if not isinstance(s["duration_seconds"], (int, float)) or s["duration_seconds"] < 0:
            out.append(f"step {s['name']!r} duration is not a non-negative number")
        for k in COUNTS:
            v = s[k]
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v < 0):
                out.append(f"step {s['name']!r} {k} is not a non-negative integer or null")
    if rec["status"] == "succeeded" and any(isinstance(s, dict) and s.get("status") != "succeeded"
                                            for s in steps):
        out.append("a succeeded run has a step that did not succeed")
    if "reconciliations" in rec:
        verdicts = rec["reconciliations"] if isinstance(rec["reconciliations"], list) else None
        if verdicts is None:
            return out + ["reconciliations is not a list"]
        ids = [v.get("id") for v in verdicts if isinstance(v, dict)]
        if len(ids) != len(set(ids)):
            out.append("a reconciliation has more than one verdict in the run")
        for v in verdicts:
            out += rc.verdict_problems(v)
        if rec["status"] == "succeeded" and any(isinstance(v, dict) and v.get("verdict") in rc.FAILING
                                                for v in verdicts):
            out.append("a succeeded run has a break or not_run reconciliation")
    return out


def history_problems(path):
    out, seen = [], set()
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError as e:
                out.append(f"line {n}: not JSON ({e.msg})")
                continue
            out += [f"line {n}: {p}" for p in line_problems(rec)]
            rid = rec.get("run_id") if isinstance(rec, dict) else None
            if rid in seen:
                out.append(f"line {n}: run_id {rid} appears twice; a rerun is a new run")
            seen.add(rid)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("exec", help="run the steps and append the record")
    ex.add_argument("--pipeline", required=True)
    ex.add_argument("--history", required=True)
    ex.add_argument("--production", action="store_true")
    ex.add_argument("--reconciliations", help="the pipeline's reconciliation declarations (ADR-0103)")
    ex.add_argument("--step", action="append", required=True, metavar="NAME=COMMAND")
    ck = sub.add_parser("check", help="validate a run history")
    ck.add_argument("history")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        problems = history_problems(a.history)
        for p in problems:
            print(p)
        print(f"{a.history}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        return 1 if problems else 0
    steps = []
    for s in a.step:
        name, sep, command = s.partition("=")
        if not sep or not name or not command:
            ap.error(f"--step {s!r} is not NAME=COMMAND")
        steps.append((name, command))
    return execute(a.pipeline, a.history, steps, production=a.production,
                   reconciliations=a.reconciliations)


if __name__ == "__main__":
    sys.exit(main())
