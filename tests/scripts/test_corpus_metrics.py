#!/usr/bin/env python3
"""Tests for scripts/python/corpus_metrics.py (#52). stdlib only."""
import json, os, subprocess, sys, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "corpus_metrics.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import corpus_metrics as cm  # noqa: E402


class Measurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = cm.build()

    def test_git_metrics_are_measured_not_assumed(self):
        g = self.m["git"]
        self.assertGreater(g["commits"], 0)
        self.assertGreaterEqual(g["active_days"], 1)
        self.assertLessEqual(g["active_days"], g["span_days"])
        self.assertIsNotNone(g["first_commit"])
        self.assertTrue(g["method"])

    def test_corpus_shape_is_measured(self):
        k = self.m["corpus"]
        for field in ("markdown_files", "markdown_lines", "executable_lines", "test_lines", "adrs"):
            self.assertGreater(k[field], 0, field)
        self.assertGreater(k["check_families"], 0)
        self.assertAlmostEqual(k["prose_to_code_ratio"],
                               round(k["markdown_lines"] / k["executable_lines"], 1), places=1)

    def test_ci_metrics_declare_availability(self):
        c = self.m["ci"]
        self.assertIn("available", c)
        if c["available"]:
            self.assertLessEqual(c["failures"], c["runs_completed"])
            if c["runs_completed"]:
                self.assertAlmostEqual(c["change_failure_rate_pct"],
                                       round(100 * c["failures"] / c["runs_completed"], 1), places=1)
        else:
            self.assertTrue(c.get("reason"), "an unavailable metric must say why")

    def test_unmeasurable_metrics_are_listed_with_a_reason(self):
        u = self.m["unavailable"]
        self.assertGreaterEqual(len(u), 3)
        for item in u:
            self.assertTrue(item["metric"]); self.assertTrue(item["reason"])

    def test_every_section_of_the_report_names_its_method(self):
        for key in ("git", "ci", "corpus"):
            block = self.m[key]
            if block.get("available") is False:
                continue
            self.assertTrue(block.get("method"), f"{key} must state how it was measured")

    def test_report_renders_and_marks_what_it_cannot_measure(self):
        text = cm.render(self.m)
        self.assertIn("# Corpus metrics", text)
        self.assertIn("Not measurable here", text)
        self.assertIn("Constitution IX", text)
        for u in self.m["unavailable"]:
            self.assertIn(u["metric"], text)

    def test_report_contains_no_estimated_ratio(self):
        """The defect this script replaces: a productivity ratio with an estimated denominator."""
        text = cm.render(self.m).lower()
        for phrase in ("human-equivalent", "speedup", "× faster", "x faster"):
            self.assertNotIn(phrase, text)

    def test_json_mode_is_machine_readable(self):
        r = subprocess.run([sys.executable, SCRIPT, "--json"], capture_output=True, text=True,
                           cwd=HERE, timeout=180)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertIn("generated_at", d); self.assertIn("git", d)

    def test_a_report_exists_on_disk(self):
        reports = [f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                   if f.startswith("corpus-metrics-") and f.endswith(".md")]
        self.assertTrue(reports, "the corpus should carry at least one measurement")


if __name__ == "__main__":
    unittest.main(verbosity=1)
