#!/usr/bin/env python3
"""Reconciliation controls for a batch run: declarations, verdicts and exceptions (ADR-0103). stdlib only.

A pipeline's spec declares each reconciliation it runs, in a JSON file beside the spec: an ID, the
two sides, the measure (a row count, the sum of a column, or the keys present on one side only),
the tolerance and an owner. The tolerance is zero unless declared. A declared one is absolute (in
the measure's unit) or relative (a share of the source side), never both, and states its reason.
Shape: docs/audit/schema/reconciliation.schema.json, `$defs/declarations`.

Each reconciliation ends a run with exactly one verdict: `match`, `within_tolerance`, `break` or
`not_run`. The verdict, both measured values and the difference go into the run record and the
step's manifest. They are aggregates: the keys behind a `break` are never written there.

    import reconcile as rc
    from run_record import Run
    declared = rc.load("specs/features/SPEC-DATA-001-o2c/reconciliations.json")
    with Run("o2c", history=..., production=True, reconciliations=declared) as run:
        ...
        with run.step("reconcile") as step:        # the run's last step: a break stops it here
            step.reconcile({"extract-vs-load": (rows_extracted, rows_loaded),
                            "erp-vs-report-total": (erp_total, report_total),
                            "invoices-both-sides": (erp_invoice_ids, report_invoice_ids)})

A `break` or `not_run` fails the step, and so the run. A reconciliation the run never reached is
`not_run`. An exception covers one reconciliation in one run. It is recorded after the run, by an
approver who is not the operator, before the outputs are relied on, and the verdict stays as it
was:

    exc = rc.exception_for(record, "erp-vs-report-total", reason="…", approver="…")
    rc.write_exception("<run dir>/exceptions", exc)   # then append it to the run's ledger

Check:

    reconcile.py check-declarations specs/features/SPEC-DATA-001-o2c/reconciliations.json
    reconcile.py relied-on <run-id> --history <history> [--exceptions DIR] [--ledger LEDGER]
        # exit 0 when the run succeeded, or failed only on reconciliations every one of which an
        # exception covers
"""
import argparse
import datetime
import decimal
import json
import os
import re
import sys

D = decimal.Decimal
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ISO = "%Y-%m-%dT%H:%M:%SZ"
DECIMAL_RE = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
MEASURES = ("row_count", "column_sum", "one_side_keys")
VERDICTS = ("match", "within_tolerance", "break", "not_run")
FAILING = ("break", "not_run")
SIDE_KINDS = ("output", "external")
DECLARATION_FIELDS = ("id", "source", "target", "measure", "column", "tolerance", "owner")
SIDE_FIELDS = ("kind", "name", "query_path")
VERDICT_FIELDS = ("id", "step", "measure", "source", "target", "difference", "verdict")
EXCEPTION_FIELDS = ("run_id", "reconciliation_id", "verdict", "difference", "reason", "approver",
                    "approved_at")


class ReconciliationFailed(Exception):
    """A reconciliation ended `break` or `not_run`: the step that ran it fails (ADR-0103 §3)."""


def _number(v):
    """An exact number. A float is refused: a sum of money in binary floating point is not exact."""
    if isinstance(v, bool) or isinstance(v, float):
        raise ValueError(f"{v!r} is not an exact number; pass an int, a Decimal or a decimal string")
    try:
        n = D(v) if isinstance(v, (int, str, D)) else None
    except decimal.InvalidOperation:
        n = None
    if n is None or not n.is_finite():
        raise ValueError(f"{v!r} is not a number")
    return n


def _side_problems(where, s):
    if not isinstance(s, dict) or set(s) != set(SIDE_FIELDS):
        return [f"{where} must have exactly {', '.join(SIDE_FIELDS)}"]
    out = []
    if s["kind"] not in SIDE_KINDS:
        out.append(f"{where} kind {s['kind']!r} is not one of {', '.join(SIDE_KINDS)}")
    if not isinstance(s["name"], str) or not s["name"]:
        out.append(f"{where} has no name")
    if s["kind"] == "external" and not (isinstance(s["query_path"], str) and s["query_path"]):
        out.append(f"{where} is an external source and needs its query path")
    if s["kind"] == "output" and s["query_path"] is not None:
        out.append(f"{where} is a step output; its query is in that step's manifest, so query_path is null")
    return out


def declaration_problems(d):
    if not isinstance(d, dict) or set(d) != set(DECLARATION_FIELDS):
        return [f"a declaration must have exactly {', '.join(DECLARATION_FIELDS)}"]
    rid = d["id"] if isinstance(d["id"], str) and ID_RE.match(d["id"]) else None
    name = rid or repr(d["id"])
    out = [] if rid else [f"id {d['id']!r} must match {ID_RE.pattern}"]
    out += _side_problems(f"{name}: source", d["source"]) + _side_problems(f"{name}: target", d["target"])
    if d["measure"] not in MEASURES:
        out.append(f"{name}: measure {d['measure']!r} is not one of {', '.join(MEASURES)}")
    elif d["measure"] == "row_count" and d["column"] is not None:
        out.append(f"{name}: a row count names no column")
    elif d["measure"] != "row_count" and not (isinstance(d["column"], str) and d["column"]):
        out.append(f"{name}: {d['measure']} needs the column it sums or keys on")
    if not isinstance(d["owner"], str) or not d["owner"]:
        out.append(f"{name}: no owner")
    t = d["tolerance"]
    if t is None:  # zero (§1)
        return out
    kinds = [k for k in ("absolute", "relative") if isinstance(t, dict) and k in t]
    if not isinstance(t, dict) or len(kinds) != 1 or set(t) != {kinds[0], "reason"}:
        return out + [f"{name}: tolerance is null (zero), or exactly one of absolute or relative, with a reason"]
    if not isinstance(t["reason"], str) or not t["reason"].strip():
        out.append(f"{name}: a tolerance states its reason")
    try:
        v = _number(t[kinds[0]])
    except ValueError as e:
        return out + [f"{name}: tolerance {e}"]
    if v <= 0:
        out.append(f"{name}: a declared tolerance is above zero; zero is the default, so leave it null")
    if kinds[0] == "absolute" and d["measure"] != "column_sum" and v != v.to_integral_value():
        out.append(f"{name}: an absolute tolerance on a count is a whole number")
    if kinds[0] == "relative" and v >= 1:
        out.append(f"{name}: a relative tolerance is a share of the source side, below 1")
    return out


def declarations_problems(doc):
    if not isinstance(doc, dict) or set(doc) != {"pipeline", "reconciliations"}:
        return ["the declarations file must have exactly pipeline, reconciliations"]
    out = [] if isinstance(doc["pipeline"], str) and ID_RE.match(doc["pipeline"]) else ["pipeline is not a valid name"]
    items = doc["reconciliations"]
    if not isinstance(items, list) or not items:
        return out + ["reconciliations must be a non-empty list"]
    seen = set()
    for d in items:
        out += declaration_problems(d)
        rid = d.get("id") if isinstance(d, dict) else None
        if isinstance(rid, str) and rid in seen:
            out.append(f"{rid}: declared twice; an ID is unique within the pipeline")
        seen.add(rid)
    return out


def load(path):
    """The declarations of a pipeline, validated. Numbers are read exactly."""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f, parse_float=D)
    problems = declarations_problems(doc)
    if problems:
        raise ValueError(f"{path}: " + "; ".join(problems))
    return doc


def judge(d, source, target, one_side=None, step=None):
    """The verdict of one declared reconciliation. A side of None means it could not be measured.

    For `one_side_keys` each side is the keys it holds, and the verdict keeps only their counts.
    A step that has already counted them passes the two counts and `one_side`, the count of keys
    on one side only.
    """
    v = dict.fromkeys(VERDICT_FIELDS)
    v.update(id=d["id"], step=step, measure=d["measure"], verdict="not_run")
    if source is None or target is None:
        return v
    if d["measure"] == "one_side_keys" and one_side is None:
        s, t = set(source), set(target)
        a, b, diff = D(len(s)), D(len(t)), D(len(s ^ t))
    elif d["measure"] == "one_side_keys":
        a, b, diff = _number(source), _number(target), _number(one_side)
    else:
        a, b = _number(source), _number(target)
        diff = b - a
    tol = d["tolerance"]
    allowed = (D(0) if tol is None else _number(tol["absolute"]) if "absolute" in tol
               else _number(tol["relative"]) * abs(a))
    v.update(source=format(a, "f"), target=format(b, "f"), difference=format(diff, "f"),
             verdict="match" if diff == 0 else "within_tolerance" if abs(diff) <= allowed else "break")
    return v


def check(doc, measured, step=None):
    """One verdict per declared reconciliation, in declared order. `measured` maps an ID to its
    (source, target), or for counted keys (source, target, one_side). A declared ID it does not
    name is `not_run`."""
    declared = {d["id"]: d for d in doc["reconciliations"]}
    unknown = sorted(set(measured) - set(declared))
    if unknown:
        raise ValueError(f"not declared: {', '.join(unknown)}")
    return [judge(d, *measured.get(rid, (None, None)), step=step) for rid, d in declared.items()]


def read_measured(path):
    """What a shell step measured: lines `id=source,target`, or `id=source,target,one_side`."""
    out = {}
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            rid, sep, values = line.strip().partition("=")
            parts = values.split(",")
            if not sep or not ID_RE.match(rid) or len(parts) not in (2, 3) or rid in out:
                raise ValueError(f"{path} line {n}: not id=source,target[,one_side], or a repeated id")
            out[rid] = tuple(p.strip() for p in parts)
    return out


def verdict_problems(v):
    if not isinstance(v, dict) or set(v) != set(VERDICT_FIELDS):
        return [f"a verdict must have exactly {', '.join(VERDICT_FIELDS)}"]
    name, out = v["id"], []
    if not isinstance(name, str) or not ID_RE.match(name):
        out.append(f"verdict id {name!r} is not a valid ID")
    if v["step"] is not None and (not isinstance(v["step"], str) or not v["step"]):
        out.append(f"{name}: step is a step name, or null when the run never reached the check")
    if v["measure"] not in MEASURES:
        out.append(f"{name}: measure {v['measure']!r} is unknown")
    if v["verdict"] not in VERDICTS:
        return out + [f"{name}: verdict {v['verdict']!r} is not one of {', '.join(VERDICTS)}"]
    values = (v["source"], v["target"], v["difference"])
    if v["verdict"] == "not_run":
        if values != (None, None, None):
            out.append(f"{name}: a not_run verdict has no measured values")
        return out
    try:
        if not all(isinstance(x, str) and DECIMAL_RE.match(x) for x in values):
            raise ValueError
        a, b, diff = (_number(x) for x in values)
    except ValueError:
        return out + [f"{name}: source, target and difference are decimal strings"]
    if (v["verdict"] == "match") != (diff == 0):
        out.append(f"{name}: match means a zero difference, and only match")
    if v["measure"] != "one_side_keys" and diff != b - a:
        out.append(f"{name}: difference is not target minus source")
    return out


def _time(s):
    return datetime.datetime.strptime(s, ISO) if isinstance(s, str) else None


def exception_for(record, reconciliation_id, reason, approver, now=None):
    """An exception for one `break` or `not_run` of one run, taken from the run's own record."""
    v = next((x for x in record.get("reconciliations") or [] if x["id"] == reconciliation_id), None)
    if v is None or v["verdict"] not in FAILING:
        raise ValueError(f"{record['run_id']}: {reconciliation_id} did not end break or not_run")
    exc = {"run_id": record["run_id"], "reconciliation_id": reconciliation_id, "verdict": v["verdict"],
           "difference": v["difference"], "reason": reason, "approver": approver,
           "approved_at": (now or datetime.datetime.now(datetime.timezone.utc)).strftime(ISO)}
    problems = exception_problems(exc, record)
    if problems:
        raise ValueError("; ".join(problems))
    return exc


def write_exception(directory, exc):
    """Write `<directory>/<reconciliation-id>.json`. One exception per reconciliation per run."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{exc['reconciliation_id']}.json")
    with open(path, "x", encoding="utf-8") as f:
        f.write(json.dumps(exc, indent=2, sort_keys=True) + "\n")
    return path


def exception_problems(exc, record):
    if not isinstance(exc, dict) or set(exc) != set(EXCEPTION_FIELDS):
        return [f"an exception must have exactly {', '.join(EXCEPTION_FIELDS)}"]
    name, out = exc["reconciliation_id"], []
    if exc["run_id"] != record["run_id"]:
        return [f"{name}: the exception is for {exc['run_id']}, not {record['run_id']}; it does not carry over"]
    v = next((x for x in record.get("reconciliations") or [] if x.get("id") == name), None)
    if v is None or v.get("verdict") not in FAILING:
        return [f"{name}: the run has no break or not_run to except"]
    if (exc["verdict"], exc["difference"]) != (v["verdict"], v["difference"]):
        out.append(f"{name}: the exception's verdict and difference are not the ones the run recorded")
    if not isinstance(exc["reason"], str) or not exc["reason"].strip():
        out.append(f"{name}: no reason")
    if not isinstance(exc["approver"], str) or not exc["approver"]:
        out.append(f"{name}: no approver")
    elif exc["approver"] == record.get("operator"):
        out.append(f"{name}: the approver is the run's operator; an exception needs a second person")
    try:
        approved, ended = _time(exc["approved_at"]), _time(record.get("ended_at"))
    except ValueError:
        approved = ended = None
    if approved is None:
        out.append(f"{name}: approved_at must be UTC {ISO}")
    elif ended is not None and approved < ended:
        out.append(f"{name}: approved before the run ended, so before the difference was known")
    return out


def reliance_problems(record, exceptions):
    """Why the run's outputs may not be relied on. Empty: they may.

    A run that succeeded may be. A run that failed may be only if every step that failed did so on
    reconciliations, and an exception covers every `break` and `not_run` (ADR-0103 §3–§4).
    """
    if record["status"] == "succeeded":
        return []
    if record["status"] == "aborted":
        return [f"{record['run_id']} was aborted"]
    verdicts = record.get("reconciliations") or []
    out = []
    reconciling = {v["step"] for v in verdicts if v["verdict"] in FAILING}
    for s in record["steps"]:
        if s["status"] != "succeeded" and s["name"] not in reconciling:
            out.append(f"step {s['name']} {s['status']}, and not on a reconciliation")
    covered = {}
    for e in exceptions:
        problems = exception_problems(e, record)
        out += problems
        if not problems:
            covered[e["reconciliation_id"]] = e
    for v in verdicts:
        if v["verdict"] in FAILING and v["id"] not in covered:
            out.append(f"{v['id']}: {v['verdict']} and no exception covers it")
    if not reconciling:
        out.append(f"{record['run_id']} failed with no break or not_run to except")
    return out


def _find(history, run_id):
    with open(history, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if rec.get("run_id") == run_id:
                    return rec
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check-declarations", help="validate a pipeline's declarations")
    c.add_argument("declarations")
    r = sub.add_parser("relied-on", help="may a run's outputs be relied on?")
    r.add_argument("run_id")
    r.add_argument("--history", required=True, help="the run history, or one run's record")
    r.add_argument("--exceptions", help="the run's exceptions directory")
    r.add_argument("--ledger", help="the run's ledger: an exception it does not list does not count")
    a = ap.parse_args(argv)
    if a.cmd == "check-declarations":
        try:
            with open(a.declarations, encoding="utf-8") as f:
                problems = declarations_problems(json.load(f, parse_float=D))
        except ValueError as e:
            problems = [f"not JSON ({e})"]
        for p in problems:
            print(p)
        print(f"{a.declarations}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        return 1 if problems else 0
    record = _find(a.history, a.run_id)
    if record is None:
        print(f"{a.run_id}: no record in {a.history}")
        return 1
    listed = None
    if a.ledger:
        with open(a.ledger, encoding="utf-8") as f:
            listed = {json.loads(l)["path"] for l in f if l.strip()}
    exceptions, problems = [], []
    if a.exceptions and os.path.isdir(a.exceptions):
        for n in sorted(os.listdir(a.exceptions)):
            p = os.path.join(a.exceptions, n)
            rel = os.path.relpath(p, os.path.dirname(os.path.abspath(a.ledger))) if a.ledger else None
            if listed is not None and rel not in listed:
                problems.append(f"{n}: not in the run's ledger, so not evidence")
                continue
            with open(p, encoding="utf-8") as f:
                exceptions.append(json.load(f))
    problems += reliance_problems(record, exceptions)
    for p in problems:
        print(p)
    print(f"{a.run_id}: {'may be relied on' if not problems else 'not to be relied on'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
