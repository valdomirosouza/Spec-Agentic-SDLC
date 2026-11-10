#!/usr/bin/env python3
"""Tests for scripts/python/reconcile.py, reconciliation controls for batch runs (ADR-0103). stdlib only."""
import copy
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "reconcile.py")
RUN_RECORD = os.path.join(HERE, "scripts", "python", "run_record.py")
SCHEMA = os.path.join(HERE, "docs", "audit", "schema", "reconciliation.schema.json")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import reconcile as rc  # noqa: E402
import run_evidence as ev  # noqa: E402
import run_record as rr  # noqa: E402

T0 = datetime.datetime(2026, 10, 31, 23, 0, 5, tzinfo=datetime.timezone.utc)
OUT = {"kind": "output", "name": "load/receivables.csv", "query_path": None}
ERP = {"kind": "external", "name": "erp", "query_path": "sql/receivables.sql"}


def decl(rid, measure="row_count", column=None, tolerance=None):
    return {"id": rid, "source": ERP, "target": OUT, "measure": measure, "column": column,
            "tolerance": tolerance, "owner": "finance-data"}


DECLARED = {"pipeline": "o2c", "reconciliations": [
    decl("extract-vs-load"),
    decl("erp-vs-report-total", "column_sum", "amount",
         {"absolute": Decimal("0.05"), "reason": "the report rounds each invoice to the cent"}),
    decl("invoices-both-sides", "one_side_keys", "invoice"),
]}


def clock():
    t = [T0]

    def now():
        t[0] += datetime.timedelta(seconds=1)
        return t[0]
    return now


class Declarations(unittest.TestCase):
    def test_the_example_declarations_are_valid(self):
        self.assertEqual(rc.declarations_problems(DECLARED), [])

    def test_a_tolerance_with_both_kinds_is_refused(self):
        d = decl("x", tolerance={"absolute": 1, "relative": Decimal("0.01"), "reason": "r"})
        self.assertTrue(any("exactly one of" in p for p in rc.declaration_problems(d)))

    def test_a_tolerance_without_a_reason_is_refused(self):
        self.assertTrue(any("reason" in p for p in rc.declaration_problems(decl("x", tolerance={"absolute": 1}))))
        d = decl("x", tolerance={"absolute": 1, "reason": "  "})
        self.assertTrue(any("states its reason" in p for p in rc.declaration_problems(d)))

    def test_a_float_tolerance_is_refused(self):
        d = decl("x", "column_sum", "amount", {"absolute": 0.05, "reason": "r"})
        self.assertTrue(any("exact" in p for p in rc.declaration_problems(d)))

    def test_a_declared_zero_tolerance_is_refused_because_zero_is_the_default(self):
        d = decl("x", tolerance={"absolute": 0, "reason": "r"})
        self.assertTrue(any("above zero" in p for p in rc.declaration_problems(d)))

    def test_an_external_side_needs_its_query_path(self):
        d = decl("x")
        d["source"] = dict(ERP, query_path=None)
        self.assertTrue(any("query path" in p for p in rc.declaration_problems(d)))

    def test_a_sum_needs_its_column(self):
        self.assertTrue(any("column" in p for p in rc.declaration_problems(decl("x", "column_sum"))))

    def test_an_id_declared_twice_is_refused(self):
        doc = {"pipeline": "o2c", "reconciliations": [decl("x"), decl("x")]}
        self.assertTrue(any("declared twice" in p for p in rc.declarations_problems(doc)))

    def test_check_declarations_reads_numbers_exactly(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "reconciliations.json")
            with open(p, "w") as f:
                f.write(json.dumps(DECLARED, default=str).replace('"0.05"', "0.05"))
            r = subprocess.run([sys.executable, SCRIPT, "check-declarations", p], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
        finally:
            shutil.rmtree(d)


class Verdicts(unittest.TestCase):
    def verdict(self, rid, source, target, *one_side):
        d = next(x for x in DECLARED["reconciliations"] if x["id"] == rid)
        return rc.judge(d, source, target, *one_side, step="reconcile")

    def test_the_four_verdicts(self):
        self.assertEqual(self.verdict("extract-vs-load", 1200, 1200)["verdict"], "match")
        self.assertEqual(self.verdict("erp-vs-report-total", "1000.00", "1000.04")["verdict"], "within_tolerance")
        self.assertEqual(self.verdict("erp-vs-report-total", "1000.00", "999.90")["verdict"], "break")
        self.assertEqual(self.verdict("extract-vs-load", None, 1200)["verdict"], "not_run")

    def test_zero_tolerance_unless_declared(self):
        self.assertEqual(self.verdict("extract-vs-load", 1200, 1199)["verdict"], "break")

    def test_the_difference_is_target_minus_source_as_an_exact_decimal(self):
        v = self.verdict("erp-vs-report-total", "1000.10", "1000.07")
        self.assertEqual((v["source"], v["target"], v["difference"]), ("1000.10", "1000.07", "-0.03"))
        self.assertEqual(rc.verdict_problems(v), [])

    def test_a_relative_tolerance_is_a_share_of_the_source(self):
        d = decl("x", tolerance={"relative": Decimal("0.001"), "reason": "late-arriving rows"})
        self.assertEqual(rc.judge(d, 10000, 9990)["verdict"], "within_tolerance")
        self.assertEqual(rc.judge(d, 10000, 9989)["verdict"], "break")

    def test_keys_are_counted_and_never_kept(self):
        v = self.verdict("invoices-both-sides", {"INV-1", "INV-2", "INV-3"}, {"INV-2", "INV-3", "INV-4"})
        self.assertEqual((v["source"], v["target"], v["difference"], v["verdict"]), ("3", "3", "2", "break"))
        self.assertNotIn("INV-1", json.dumps(v))

    def test_a_float_value_is_refused(self):
        with self.assertRaises(ValueError):
            self.verdict("erp-vs-report-total", 1000.0, 1000.04)

    def test_every_declared_reconciliation_gets_one_verdict(self):
        vs = rc.check(DECLARED, {"extract-vs-load": (5, 5)})
        self.assertEqual([v["verdict"] for v in vs], ["match", "not_run", "not_run"])
        with self.assertRaises(ValueError):
            rc.check(DECLARED, {"undeclared": (1, 1)})

    def test_a_match_with_a_difference_is_caught(self):
        v = dict(self.verdict("extract-vs-load", 5, 6), verdict="match")
        self.assertTrue(any("match means" in p for p in rc.verdict_problems(v)))


class InARun(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.history = os.path.join(tempfile.mkdtemp(), "history.jsonl")
        git = ["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        subprocess.run(git + ["commit", "-q", "--allow-empty", "-m", "init"], check=True)

    def tearDown(self):
        shutil.rmtree(self.repo)
        shutil.rmtree(os.path.dirname(self.history))

    def run_(self):
        return rr.Run("o2c", self.history, repo=self.repo, operator="ops", now=clock(),
                      reconciliations=DECLARED)

    def record(self):
        (rec,) = [json.loads(l) for l in open(self.history)]
        self.assertEqual(rr.line_problems(rec), [])
        return rec

    def reconcile(self, total_target):
        with self.run_() as run:
            with run.step("reconcile") as step:
                step.reconcile({"extract-vs-load": (3, 3), "erp-vs-report-total": ("60.00", total_target),
                                "invoices-both-sides": ({"1", "2", "3"}, {"1", "2", "3"})})

    def test_a_run_whose_reconciliations_agree_succeeds(self):
        self.reconcile("60.03")
        rec = self.record()
        self.assertEqual(rec["status"], "succeeded")
        self.assertEqual([v["verdict"] for v in rec["reconciliations"]], ["match", "within_tolerance", "match"])

    def test_a_break_fails_the_step_and_the_run_and_is_recorded(self):
        with self.assertRaises(rc.ReconciliationFailed):
            self.reconcile("59.00")
        rec = self.record()
        self.assertEqual((rec["status"], rec["steps"][0]["status"]), ("failed", "failed"))
        self.assertEqual(rec["reconciliations"][1]["verdict"], "break")

    def test_a_reconciliation_the_run_never_reached_is_not_run(self):
        with self.run_() as run:
            with run.step("reconcile") as step:
                step.reconcile({"extract-vs-load": (3, 3)})
        rec = self.record()
        self.assertEqual(rec["status"], "failed")
        self.assertEqual([(v["step"], v["verdict"]) for v in rec["reconciliations"]],
                         [("reconcile", "match"), (None, "not_run"), (None, "not_run")])

    def test_a_succeeded_run_with_a_break_in_the_history_is_caught(self):
        self.reconcile("60.00")
        rec = self.record()
        rec["reconciliations"][0] = dict(rec["reconciliations"][0], source="2", difference="1", verdict="break")
        self.assertTrue(any("break or not_run" in p for p in rr.line_problems(rec)))

    def test_the_verdicts_go_into_the_step_manifest(self):
        verdicts = rc.check(DECLARED, {"extract-vs-load": (3, 3)}, step="reconcile")[:1]
        m = ev.manifest("o2c-20261031T230006Z", "a" * 40, "reconcile", inputs=[ev.source("erp")], outputs=[],
                        reconciliations=verdicts)
        self.assertEqual(ev.manifest_problems(m), [])
        m["step"] = "load"
        self.assertTrue(any("another step" in p for p in ev.manifest_problems(m)))

    def test_a_shell_step_reports_what_it_measured(self):
        decls = os.path.join(self.repo, "..", os.path.basename(self.repo) + "-reconciliations.json")
        with open(decls, "w") as f:
            json.dump(DECLARED, f, default=str)
        try:
            step = ("sh -c 'printf \"extract-vs-load=3,3\\nerp-vs-report-total=60.00,60.00\\n"
                    "invoices-both-sides=3,3,1\\n\" > \"$RUN_RECONCILIATIONS\"'")
            r = subprocess.run([sys.executable, RUN_RECORD, "exec", "--pipeline", "o2c", "--history", self.history,
                                "--reconciliations", decls, "--step", f"reconcile={step}"],
                               cwd=self.repo, capture_output=True, text=True)
        finally:
            os.remove(decls)
        self.assertEqual(r.returncode, 1, r.stderr)
        rec = self.record()
        self.assertEqual([v["verdict"] for v in rec["reconciliations"]], ["match", "match", "break"])


class Exceptions(unittest.TestCase):
    def setUp(self):
        verdicts = rc.check(DECLARED, {"extract-vs-load": (3, 3), "erp-vs-report-total": ("60.00", "59.00"),
                                       "invoices-both-sides": ({"1"}, {"1"})}, step="reconcile")
        self.record = {"run_id": "o2c-20261031T230006Z", "operator": "ops", "status": "failed",
                       "ended_at": "2026-10-31T23:00:09Z", "reconciliations": verdicts,
                       "steps": [{"name": "extract", "status": "succeeded"},
                                 {"name": "reconcile", "status": "failed"}]}
        self.when = datetime.datetime(2026, 11, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

    def exc(self, **kw):
        args = dict(reason="credit note posted after the extract", approver="controller", now=self.when)
        args.update(kw)
        return rc.exception_for(self.record, "erp-vs-report-total", **args)

    def test_an_exception_takes_the_recorded_verdict_and_difference(self):
        e = self.exc()
        self.assertEqual((e["verdict"], e["difference"]), ("break", "-1.00"))
        self.assertEqual(rc.reliance_problems(self.record, [e]), [])

    def test_the_verdict_is_never_rewritten(self):
        before = copy.deepcopy(self.record)
        self.exc()
        self.assertEqual(self.record, before)

    def test_the_operator_cannot_approve(self):
        with self.assertRaisesRegex(ValueError, "second person"):
            self.exc(approver="ops")

    def test_only_a_break_or_not_run_can_be_excepted(self):
        with self.assertRaises(ValueError):
            rc.exception_for(self.record, "extract-vs-load", reason="r", approver="controller", now=self.when)

    def test_an_exception_does_not_carry_over_to_the_next_run(self):
        e = self.exc()
        nxt = dict(self.record, run_id="o2c-20261130T230006Z")
        self.assertTrue(any("does not carry over" in p for p in rc.reliance_problems(nxt, [e])))

    def test_an_exception_for_another_difference_does_not_cover(self):
        e = dict(self.exc(), difference="-0.50")
        self.assertTrue(any("not the ones the run recorded" in p for p in rc.reliance_problems(self.record, [e])))

    def test_an_exception_approved_before_the_run_ended_is_refused(self):
        with self.assertRaisesRegex(ValueError, "before the run ended"):
            self.exc(now=datetime.datetime(2026, 10, 31, 23, 0, 0, tzinfo=datetime.timezone.utc))

    def test_an_uncovered_break_or_another_failed_step_blocks_reliance(self):
        self.assertTrue(any("no exception covers" in p for p in rc.reliance_problems(self.record, [])))
        other = dict(self.record, steps=[{"name": "load", "status": "failed"}, self.record["steps"][1]])
        self.assertTrue(any("not on a reconciliation" in p for p in rc.reliance_problems(other, [self.exc()])))

    def test_relied_on_ignores_an_exception_missing_from_the_ledger(self):
        d = tempfile.mkdtemp()
        try:
            history = os.path.join(d, "run-record.json")
            with open(history, "w") as f:
                f.write(json.dumps(self.record) + "\n")
            path = rc.write_exception(os.path.join(d, "exceptions"), self.exc())
            with self.assertRaises(FileExistsError):
                rc.write_exception(os.path.join(d, "exceptions"), self.exc())
            cmd = [sys.executable, SCRIPT, "relied-on", self.record["run_id"], "--history", history,
                   "--exceptions", os.path.join(d, "exceptions"), "--ledger", os.path.join(d, "ledger.jsonl")]
            ev.append(os.path.join(d, "ledger.jsonl"), self.record["run_id"], "reconcile", path)
            r = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)  # listed by its absolute path, not relative to the run
            self.assertIn("not in the run's ledger", r.stdout)
            os.remove(os.path.join(d, "ledger.jsonl"))
            cwd = os.getcwd()
            os.chdir(d)
            try:
                ev.append("ledger.jsonl", self.record["run_id"], "reconcile", "exceptions/erp-vs-report-total.json")
            finally:
                os.chdir(cwd)
            r = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("may be relied on", r.stdout)
        finally:
            shutil.rmtree(d)


class Schema(unittest.TestCase):
    """Two descriptions of one record drift unless something compares them."""

    def test_the_schema_and_the_script_name_the_same_fields(self):
        with open(SCHEMA) as f:
            defs = json.load(f)["$defs"]
        self.assertEqual(defs["declaration"]["required"], list(rc.DECLARATION_FIELDS))
        self.assertEqual(defs["side"]["required"], list(rc.SIDE_FIELDS))
        self.assertEqual(defs["verdict"]["required"], list(rc.VERDICT_FIELDS))
        self.assertEqual(defs["exception"]["required"], list(rc.EXCEPTION_FIELDS))
        self.assertEqual(defs["verdict"]["properties"]["verdict"]["enum"], list(rc.VERDICTS))
        self.assertEqual(defs["declaration"]["properties"]["measure"]["enum"], list(rc.MEASURES))
        self.assertEqual(defs["decimal"]["pattern"], rc.DECIMAL_RE.pattern)


if __name__ == "__main__":
    unittest.main(verbosity=1)
