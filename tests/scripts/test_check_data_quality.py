#!/usr/bin/env python3
"""Tests for scripts/python/check_data_quality.py (#53). stdlib only."""
import json, os, subprocess, sys, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "check_data_quality.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import check_data_quality as dq  # noqa: E402

DIMENSIONS = {"completeness", "validity", "accuracy", "consistency", "uniqueness", "timeliness"}
SEVERITIES = {"critical", "major", "minor"}
ACTIONS = {"block", "alert", "record"}


class RuleShape(unittest.TestCase):
    """specs/data/data-quality.md §3: every rule carries the same fields, or it is not a rule."""

    def test_every_rule_has_the_required_fields(self):
        self.assertGreaterEqual(len(dq.RULES), 10)
        for r in dq.RULES:
            for f in ("id", "dataset", "dimension", "rule", "measure", "threshold", "severity", "on_violation"):
                self.assertTrue(r.get(f), f"{r.get('id')} missing {f}")

    def test_dimensions_severities_and_actions_are_from_the_spec(self):
        for r in dq.RULES:
            self.assertIn(r["dimension"], DIMENSIONS, r["id"])
            self.assertIn(r["severity"], SEVERITIES, r["id"])
            self.assertIn(r["on_violation"], ACTIONS, r["id"])

    def test_rule_ids_are_unique(self):
        ids = [r["id"] for r in dq.RULES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_critical_rules_block(self):
        """The spec: a critical violation stops the pipeline; it cannot be a mere alert."""
        for r in dq.RULES:
            if r["severity"] == "critical":
                self.assertEqual(r["on_violation"], "block", r["id"])

    def test_all_six_dimensions_are_covered(self):
        self.assertEqual({r["dimension"] for r in dq.RULES}, DIMENSIONS)

    def test_more_than_one_dataset_is_measured(self):
        self.assertGreaterEqual(len({r["dataset"] for r in dq.RULES}), 4)


class Evaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = dq.evaluate()

    def test_every_rule_evaluates_without_erroring(self):
        for r in self.results:
            self.assertNotEqual(r["violations"], -1, f"{r['id']} failed to evaluate: {r['detail']}")

    def test_a_violation_always_carries_a_detail(self):
        """A count with no explanation is not actionable."""
        for r in self.results:
            if not r["ok"]:
                self.assertTrue(r["detail"], r["id"])

    def test_no_critical_rule_is_violated(self):
        crit = [r for r in self.results if r["severity"] == "critical" and not r["ok"]]
        self.assertEqual(crit, [], f"critical data-quality violations: {crit}")

    def test_exit_code_counts_only_blocking_severities(self):
        r = subprocess.run([sys.executable, SCRIPT, "--run", "--quiet"], capture_output=True,
                           text=True, cwd=HERE, timeout=120)
        blocking = [x for x in self.results if not x["ok"] and x["severity"] in ("critical", "major")]
        self.assertEqual(r.returncode, len(blocking))

    def test_json_mode_is_machine_readable(self):
        r = subprocess.run([sys.executable, SCRIPT, "--run", "--json"], capture_output=True,
                           text=True, cwd=HERE, timeout=120)
        data = json.loads(r.stdout)
        self.assertEqual(len(data), len(dq.RULES))
        self.assertIn("violations", data[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
