#!/usr/bin/env python3
"""Tests for scripts/python/corpus_metrics.py (#52). stdlib only."""
import json, os, re, subprocess, sys, unittest

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
        self.assertEqual(k["verification_lines"], k["executable_lines"] + k["test_lines"])
        self.assertAlmostEqual(k["prose_to_verification_ratio"],
                               round(k["markdown_lines"] / k["verification_lines"], 1), places=1)

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

    def test_report_states_no_ratio_rather_than_computing_one(self):
        """The defect this script replaces: a productivity ratio with an estimated denominator.

        The report may DISCUSS why there is no ratio — the first version of this test forbade the
        word and so forbade the explanation too. What it must not contain is a computed one."""
        text = cm.render(self.m)
        self.assertIn("no speedup ratio", text.lower())
        self.assertIn("What a legitimate ratio would require", text)
        import re as _re
        claimed = _re.search(r"(speedup ratio|human-equiv[^|\n]*÷)[^|\n]*\d+(\.\d+)?\s*[×x]", text)
        self.assertIsNone(claimed, f"the report computes a ratio: {claimed.group(0) if claimed else ''}")

    def test_the_measured_side_is_reported(self):
        t = self.m.get("session", {})
        self.assertTrue(t.get("available"))
        self.assertGreater(t["commits"], 0)
        self.assertTrue(t["method"])
        self.assertTrue(t["not_a_ratio"])

    def test_json_mode_is_machine_readable(self):
        r = subprocess.run([sys.executable, SCRIPT, "--json"], capture_output=True, text=True,
                           cwd=HERE, timeout=180)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertIn("generated_at", d); self.assertIn("git", d)

    def test_check_mode_detects_a_stale_report(self):
        """R4-T6. There was no --check, so nothing could fail on a stale or wrong report."""
        import shutil, tempfile
        latest = sorted(f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                        if f.startswith("corpus-metrics-"))[-1]
        path = os.path.join(HERE, "docs", "sre", latest)
        backup = tempfile.mktemp(); shutil.copy(path, backup)
        try:
            # Refresh first: this test is about what --check does, not about whether the report
            # committed yesterday is current. Asserting the repo's freshness here made the test red
            # every time the verifier itself gained a line, which is a false signal.
            subprocess.run([sys.executable, SCRIPT, "--report"],
                           capture_output=True, cwd=HERE, timeout=180, check=True)
            self.assertEqual(subprocess.run([sys.executable, SCRIPT, "--check", "--quiet"],
                                            capture_output=True, cwd=HERE, timeout=180).returncode, 0)
            text = open(path, encoding="utf-8").read().replace("## 3. Corpus shape", "## 3. Removed")
            open(path, "w", encoding="utf-8").write(text)
            self.assertEqual(subprocess.run([sys.executable, SCRIPT, "--check", "--quiet"],
                                            capture_output=True, cwd=HERE, timeout=180).returncode, 1)
        finally:
            shutil.copy(backup, path); os.unlink(backup)

    def test_drift_reports_a_move_and_stays_quiet_otherwise(self):
        """R5-T7. The scheduled run needs a comparison that tolerates a legitimately days-old
        report: --check is exact because a report committed with a change must match it, and an
        issue opened for every one-line edit is noise that gets muted."""
        import shutil, tempfile
        latest = sorted(f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                        if f.startswith("corpus-metrics-"))[-1]
        path = os.path.join(HERE, "docs", "sre", latest)
        backup = tempfile.mktemp(); shutil.copy(path, backup)
        body = tempfile.mktemp(suffix=".md")
        try:
            subprocess.run([sys.executable, SCRIPT, "--report"],
                           capture_output=True, cwd=HERE, timeout=180, check=True)
            r = subprocess.run([sys.executable, SCRIPT, "--drift"],
                               capture_output=True, text=True, cwd=HERE, timeout=180)
            self.assertEqual(r.returncode, 0, f"a current report must not report drift: {r.stdout}")

            text = open(path, encoding="utf-8").read()
            doctored = re.sub(r"^\| ADRs \| [0-9]+ \|", "| ADRs | 1 |", text, count=1, flags=re.M)
            self.assertNotEqual(doctored, text, "the ADRs row must be present to doctor")
            open(path, "w", encoding="utf-8").write(doctored)
            r = subprocess.run([sys.executable, SCRIPT, "--drift", "--body-out", body],
                               capture_output=True, text=True, cwd=HERE, timeout=180)
            self.assertEqual(r.returncode, 1)
            self.assertIn("ADRs", r.stdout)
            self.assertIn("| Metric | Published | Live | Move |", open(body, encoding="utf-8").read(),
                          "the issue body must carry the delta, not just an exit code")
        finally:
            shutil.copy(backup, path); os.unlink(backup)
            if os.path.exists(body):
                os.unlink(body)

    def test_check_families_matches_what_actually_runs(self):
        """R4-T6. The count was `grep -c '^say \"C'` and reported 12 while 15 families ran."""
        import re
        src = open(os.path.join(HERE, "scripts", "bash", "check-corpus.sh"), encoding="utf-8").read()
        self.assertEqual(self.m["corpus"]["check_families"], len(set(re.findall(r'say "(C\d+)', src))))

    def test_a_report_exists_on_disk(self):
        reports = [f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                   if f.startswith("corpus-metrics-") and f.endswith(".md")]
        self.assertTrue(reports, "the corpus should carry at least one measurement")


if __name__ == "__main__":
    unittest.main(verbosity=1)
