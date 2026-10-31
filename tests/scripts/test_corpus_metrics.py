#!/usr/bin/env python3
"""Tests for scripts/python/corpus_metrics.py (#52). stdlib only."""
import json, os, re, subprocess, sys, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "corpus_metrics.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import corpus_metrics as cm  # noqa: E402


def metrics(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                          cwd=HERE, timeout=180)


class Measurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = cm.build()

    def setUp(self):
        # Reports are read and written here, never in docs/sre: the tests used to leave today's
        # report in the working tree, and their verdict depended on the date and on which real
        # reports existed (#120).
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.reports = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def write_report(self):
        """Render a current report into the scratch directory; returns (path, its date)."""
        metrics("--report", "--reports-dir", self.reports).check_returncode()
        name = sorted(f for f in os.listdir(self.reports) if f.startswith("corpus-metrics-"))[-1]
        return os.path.join(self.reports, name), "-".join(cm._REPORT_DATE.search(name).groups())

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
        # A fresh report first: this test is about what --check does, not about whether the report
        # committed yesterday is current. Asserting the repo's freshness here made the test red
        # every time the verifier itself gained a line, which is a false signal.
        path, _ = self.write_report()
        self.assertEqual(metrics("--check", "--quiet", "--reports-dir", self.reports).returncode, 0)
        text = open(path, encoding="utf-8").read().replace("## 3. Corpus shape", "## 3. Removed")
        open(path, "w", encoding="utf-8").write(text)
        self.assertEqual(metrics("--check", "--quiet", "--reports-dir", self.reports).returncode, 1)

    def test_drift_refuses_when_no_baseline_is_old_enough(self):
        """R6-T1. Comparing against the NEWEST report made the scheduled job structurally unable to
        find anything: check-corpus forces that report to equal the live numbers on every commit,
        so the comparison measured a number against itself and answered `no movement`, for ever.
        With no baseline old enough the honest answer is a refusal, not an all-clear."""
        _, published = self.write_report()
        r = metrics("--drift", "--reports-dir", self.reports, "--today", published)
        self.assertEqual(r.returncode, 2, f"expected a refusal, got: {r.stdout}{r.stderr}")
        self.assertIn("no baseline", r.stdout)

    def test_drift_compares_against_an_older_report_and_sees_activity(self):
        """The baseline must be old enough for something to have happened, and the comparison must
        include the numbers that move WITHOUT anyone editing a file. Those were excluded entirely,
        which left drift watching only the rows the commit gate pins."""
        path, _ = self.write_report()
        text = open(path, encoding="utf-8").read()
        os.unlink(path)
        text = re.sub(r"^\| ADRs \| [0-9]+ \|", "| ADRs | 1 |", text, count=1, flags=re.M)
        text = re.sub(r"^\| Commits on the default branch \| [0-9]+ \|",
                      "| Commits on the default branch | 1 |", text, count=1, flags=re.M)
        # The only report, exactly the minimum age old on the date this run claims to be.
        base = os.path.join(self.reports, "corpus-metrics-2026-08-15.md")
        open(base, "w", encoding="utf-8").write(text)
        body = os.path.join(self.reports, "body.md")
        r = metrics("--drift", "--reports-dir", self.reports, "--today", "2026-08-22",
                    "--body-out", body)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("ADRs", r.stdout, "a structural row must still be compared")
        self.assertIn("Commits on the default branch", r.stdout,
                      "an activity row is the whole reason a periodic comparison exists")
        self.assertIn("| Metric | Published | Live | Move |", open(body, encoding="utf-8").read())

    def test_the_baseline_is_the_newest_report_old_enough_not_the_newest_overall(self):
        import datetime
        today = datetime.date(2026, 9, 13)
        picked = cm.baseline_report(7, today)
        self.assertIsNone(picked, "today's report is the only one and it is not old enough")

    def test_the_published_sensitivity_table_matches_the_real_threshold(self):
        """A document advertising a sensitivity the tool does not have is the same defect as a
        check that cannot fail, one step removed."""
        # Regenerate first. This test file counts toward `Test lines`, so asserting against the
        # committed report made the test fail whenever it grew — a fact about the repository, not
        # about the behaviour under test. Same trap as the stale-report case above.
        path, _ = self.write_report()
        on_disk = open(path, encoding="utf-8").read()
        self.assertIn(f"**{cm.DEFAULT_THRESHOLD_PCT}%**", on_disk)
        self.assertIn(f"**{cm.DEFAULT_BASELINE_AGE_DAYS} days**", on_disk)
        m = cm.build()
        for label, live in cm.structural_rows(m):
            want = max(1, round(live * cm.DEFAULT_THRESHOLD_PCT / 100.0))
            self.assertIn(f"| {label} | {live} | {want} |", on_disk, label)

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
