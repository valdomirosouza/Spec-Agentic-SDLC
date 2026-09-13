#!/usr/bin/env python3
"""Tests for .github/workflows/corpus-measure.yml (#74). stdlib only.

A scheduled job is the one kind of code nobody runs while writing it. The first version of this
workflow shipped with three defects that a single read would not surface and that no gate could:
it compared against a baseline the commit gate pins, it measured without a token so the archived
report lost its CI rows, and it never returned the report to the repository so a second data point
could never exist. These assertions are the substitute for being able to execute it.
"""
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WF = os.path.join(HERE, ".github", "workflows", "corpus-measure.yml")
SCRIPT = os.path.join(HERE, "scripts", "python", "corpus_metrics.py")


def text():
    with open(WF, encoding="utf-8") as fh:
        return fh.read()


def commands(t):
    """Every `corpus_metrics.py …` invocation, continuation lines joined, comments dropped.

    Scanning the raw file matched my own explanatory comments and the flags of unrelated `gh`
    calls, which is how the first version of this test reported failures that were not there."""
    body = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("#"))
    body = re.sub(r"\\\n\s*", " ", body)
    return [l.strip() for l in body.split("\n") if "corpus_metrics.py" in l]


class Wiring(unittest.TestCase):
    def setUp(self):
        self.t = text()

    def test_it_is_actually_scheduled(self):
        # assertRegex's third argument is the failure message, not flags — compile instead.
        for pat in (r"^on:", r"^  schedule:", r"^    - cron:"):
            self.assertRegex(self.t, re.compile(pat, re.M))

    def test_the_token_is_declared_for_every_step_not_just_the_last(self):
        """R6-T2. Declared on the issue step alone, `gh run list` failed inside the measurement and
        the archived report silently lost its CI rows — the rows --check is told to ignore, so
        nothing could have caught it."""
        before_steps = self.t.split("steps:")[0]
        self.assertIn("GH_TOKEN", before_steps,
                      "GH_TOKEN must be declared at job level, above the first step")

    def test_the_body_the_drift_step_writes_is_the_body_the_issue_step_reads(self):
        """Two literal paths drift apart silently; one variable cannot."""
        self.assertIn('--body-out "$DRIFT_BODY"', self.t)
        self.assertIn('"$DRIFT_BODY"', self.t.split("File what moved")[1],
                      "the issue step must read the same file the drift step wrote")

    def test_the_issue_is_filed_only_when_something_moved(self):
        self.assertIn("if: steps.drift.outputs.rc != '0'", self.t)

    def test_drift_runs_before_the_report_is_regenerated(self):
        """--report writes a file dated today. Generating first would add a baseline zero days old
        and the comparison would have to refuse every time."""
        cmds = commands(self.t)
        order = [("--drift" in c, "--report" in c) for c in cmds]
        self.assertTrue(any(d for d, _ in order), "no --drift invocation found")
        first_drift = next(i for i, (d, _) in enumerate(order) if d)
        first_report = next(i for i, (_, r) in enumerate(order) if r)
        self.assertLess(first_drift, first_report,
                        "measuring after regenerating makes the baseline useless")

    def test_the_report_is_proposed_back_so_a_series_can_form(self):
        """Archiving to a build artifact alone leaves exactly one dated report on disk for ever,
        and a comparison with one point is not a comparison."""
        self.assertIn("gh pr create", self.t)
        self.assertIn("--base main", self.t)

    def test_it_never_merges_deploys_or_writes_to_main(self):
        """Constitution V. The workflow prepares and recommends; a human lands it."""
        forbidden = [r"gh pr merge", r"gh release create", r"git push[^\n]*origin main",
                     r"git push[^\n]*HEAD:main", r"--auto\b", r"--admin\b"]
        for pat in forbidden:
            self.assertNotRegex(self.t, re.compile(pat), f"workflow must not do this: {pat}")

    def test_every_flag_it_passes_exists_in_the_tool(self):
        """A renamed flag turns the weekly run into a weekly crash that nobody is watching."""
        helptext = subprocess.run([sys.executable, SCRIPT, "--help"],
                                  capture_output=True, text=True, cwd=HERE, timeout=60).stdout
        flags = set()
        for cmd in commands(self.t):
            flags.update(re.findall(r"(?<![\w-])--[a-z][a-z-]+", cmd))
        self.assertTrue(flags, "expected to find the flags the workflow passes")
        for f in sorted(flags):
            # Whole token, not substring. `assertIn` passed a renamed `--baseline-age` because the
            # help text still contained `--baseline-age-days`, so the check could not catch the one
            # mutation it exists for. Found by injecting exactly that rename.
            self.assertRegex(
                helptext, re.compile(rf"(?<![\w-]){re.escape(f)}(?![\w-])"),
                f"{f} is passed by the workflow but the tool has no such flag")


if __name__ == "__main__":
    unittest.main(verbosity=1)
