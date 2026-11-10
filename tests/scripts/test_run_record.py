#!/usr/bin/env python3
"""Tests for scripts/python/run_record.py, the batch run record (ADR-0101). stdlib only."""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "run_record.py")
SCHEMA = os.path.join(HERE, "docs", "sre", "slo", "schema", "run-record.schema.json")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import run_record as rr  # noqa: E402

T0 = datetime.datetime(2026, 10, 31, 23, 0, 5, tzinfo=datetime.timezone.utc)


def clock():
    """Each call is one second after the last, so started_at and ended_at differ."""
    t = [T0]

    def now():
        t[0] += datetime.timedelta(seconds=1)
        return t[0]
    return now


class RunRecord(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        self.history = os.path.join(tempfile.mkdtemp(), "runs", "history.jsonl")
        git = ["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run(["git", "init", "-q", self.repo], check=True)
        open(os.path.join(self.repo, "extract.sql"), "w").write("select 1;\n")
        subprocess.run(git + ["add", "."], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "init"], check=True)
        self.head = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"],
                                   capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        shutil.rmtree(self.repo)
        shutil.rmtree(os.path.dirname(os.path.dirname(self.history)))

    def run_(self, **kw):
        return rr.Run("o2c", self.history, repo=self.repo, operator="ops", now=clock(), **kw)

    def records(self):
        return [json.loads(l) for l in open(self.history)]

    def test_a_succeeded_run_records_its_commit_and_steps(self):
        with self.run_() as run:
            with run.step("extract") as s:
                s.count(rows_in=10, rows_out=9, rows_rejected=1)
        (rec,) = self.records()
        self.assertEqual(rec["run_id"], "o2c-20261031T230006Z")
        self.assertEqual((rec["commit"], rec["dirty"], rec["status"]), (self.head, False, "succeeded"))
        self.assertEqual(rec["steps"][0]["rows_rejected"], 1)
        self.assertEqual(rr.history_problems(self.history), [])

    def test_a_failed_run_is_still_recorded(self):
        """ADR-0101 §2: the failure is the case the record exists for."""
        with self.assertRaises(ValueError):
            with self.run_() as run:
                with run.step("extract"):
                    pass
                with run.step("load"):
                    raise ValueError("load broke")
        (rec,) = self.records()
        self.assertEqual(rec["status"], "failed")
        self.assertEqual([(s["name"], s["status"]) for s in rec["steps"]],
                         [("extract", "succeeded"), ("load", "failed")])

    def test_an_interrupted_run_is_aborted(self):
        with self.assertRaises(KeyboardInterrupt):
            with self.run_() as run:
                with run.step("extract"):
                    raise KeyboardInterrupt
        self.assertEqual(self.records()[0]["status"], "aborted")

    def test_a_production_run_from_a_dirty_tree_is_refused_and_recorded(self):
        open(os.path.join(self.repo, "hotfix.sql"), "w").write("update x;\n")
        with self.assertRaises(rr.RunRefused):
            with self.run_(production=True):
                self.fail("a refused run must not reach its first step")
        (rec,) = self.records()
        self.assertEqual((rec["status"], rec["dirty"], rec["steps"]), ("aborted", True, []))
        self.assertEqual(rr.history_problems(self.history), [])

    def test_a_non_production_run_from_a_dirty_tree_is_marked(self):
        open(os.path.join(self.repo, "hotfix.sql"), "w").write("update x;\n")
        with self.run_():
            pass
        self.assertEqual((self.records()[0]["dirty"], self.records()[0]["status"]), (True, "succeeded"))

    def test_outside_a_repository_there_is_no_run(self):
        """No commit means nothing ties the run to code, so it never starts."""
        bare = tempfile.mkdtemp()
        try:
            with self.assertRaises(rr.RunRefused):
                with rr.Run("o2c", self.history, repo=bare, now=clock()):
                    pass
        finally:
            shutil.rmtree(bare)

    def test_a_bad_pipeline_name_is_rejected(self):
        with self.assertRaises(ValueError):
            rr.Run("O2C close", self.history)

    def test_exec_runs_shell_steps_and_reads_their_counts(self):
        step = os.path.join(self.repo, "count.sh")
        open(step, "w").write('#!/bin/sh\necho rows_in=5 > "$RUN_STEP_COUNTS"\necho rows_out=5 >> "$RUN_STEP_COUNTS"\n')
        os.chmod(step, 0o755)
        subprocess.run(["git", "-C", self.repo, "add", "count.sh"], check=True)
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "commit", "-q", "-m", "step"], check=True)
        rc = rr.execute("o2c", self.history, [("extract", f"sh {step}"), ("fail", "sh -c 'exit 3'"),
                                               ("never", "true")], production=True, repo=self.repo)
        self.assertEqual(rc, 1)
        (rec,) = self.records()
        self.assertEqual(rec["status"], "failed")
        self.assertEqual([s["name"] for s in rec["steps"]], ["extract", "fail"])
        self.assertEqual((rec["steps"][0]["rows_in"], rec["steps"][0]["rows_out"]), (5, 5))

    def test_exec_reports_a_missing_command_as_a_failed_step(self):
        rc = rr.execute("o2c", self.history, [("extract", "no-such-command-anywhere")], repo=self.repo)
        self.assertEqual(rc, 1)
        self.assertEqual(self.records()[0]["steps"][0]["status"], "failed")


class Check(unittest.TestCase):
    GOOD = {"run_id": "o2c-20261031T230005Z", "pipeline": "o2c", "commit": "a" * 40, "dirty": False,
            "production": True, "operator": "ops", "started_at": "2026-10-31T23:00:05Z",
            "ended_at": "2026-10-31T23:10:00Z", "status": "succeeded",
            "steps": [{"name": "extract", "status": "succeeded", "duration_seconds": 1.5,
                       "rows_in": 3, "rows_out": 3, "rows_rejected": None}]}

    def problems(self, **change):
        return rr.line_problems({**self.GOOD, **change})

    def test_a_good_record_has_no_problems(self):
        self.assertEqual(self.problems(), [])

    def test_a_run_id_that_does_not_match_its_start_is_caught(self):
        self.assertTrue(any("run_id" in p for p in self.problems(run_id="o2c-20261101T000000Z")))

    def test_a_short_commit_is_caught(self):
        self.assertTrue(any("commit" in p for p in self.problems(commit="abc1234")))

    def test_a_dirty_production_run_that_ran_is_caught(self):
        self.assertTrue(any("dirty" in p for p in self.problems(dirty=True)))

    def test_a_succeeded_run_with_a_failed_step_is_caught(self):
        steps = [{**self.GOOD["steps"][0], "status": "failed"}]
        self.assertTrue(any("succeeded run" in p for p in self.problems(steps=steps)))

    def test_a_data_value_field_is_caught(self):
        """The record holds counts and identifiers; an extra field is where a value would leak in."""
        self.assertTrue(any("unknown field" in p for p in self.problems(customer="x")))

    def test_a_duplicate_run_id_is_caught(self):
        d = tempfile.mkdtemp()
        try:
            p = os.path.join(d, "h.jsonl")
            open(p, "w").write((json.dumps(self.GOOD) + "\n") * 2)
            self.assertTrue(any("appears twice" in x for x in rr.history_problems(p)))
            r = subprocess.run([sys.executable, SCRIPT, "check", p], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)
        finally:
            shutil.rmtree(d)

    def test_the_schema_and_the_script_name_the_same_fields(self):
        """Two descriptions of one record drift unless something compares them."""
        schema = json.load(open(SCHEMA))
        self.assertEqual(schema["required"], list(rr.FIELDS))
        self.assertEqual(schema["properties"]["status"]["enum"], list(rr.RUN_STATUSES))
        item = schema["properties"]["steps"]["items"]
        self.assertEqual(item["required"], list(rr.STEP_FIELDS))
        self.assertEqual(item["properties"]["status"]["enum"], list(rr.STEP_STATUSES))


if __name__ == "__main__":
    unittest.main(verbosity=1)
