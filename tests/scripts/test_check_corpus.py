#!/usr/bin/env python3
"""Mutation tests for scripts/bash/check-corpus.sh — prove each check can actually fail (#66).

The corpus verifies its content with 50 assertions and never verified the verifier. Nothing fed a
check the defect it exists to catch, so a check written in haste was indistinguishable from one
that works: both stayed green. That is how three vacuous checks shipped in one round and two more
in the next.

Each case below applies a real mutation, runs check-corpus.sh, and requires that it fail AND that
the failure name the problem. A mutation that leaves the check green is the bug this file reports.

Restoration is guaranteed by try/finally per case, and a final guard asserts the tree is clean.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHECK = os.path.join(HERE, "scripts", "bash", "check-corpus.sh")


def run_check(*extra):
    """check-corpus.sh with the slow sub-suites off: a mutation test runs it many times."""
    r = subprocess.run(["bash", CHECK, "--no-smoke", *extra], capture_output=True, text=True,
                       cwd=HERE, timeout=300)
    return r.returncode, r.stdout + r.stderr


class Mutation:
    """Edit a file, restore it whatever happens."""

    def __init__(self, rel, before, after, *, regex=False):
        self.path = os.path.join(HERE, rel)
        self.rel, self.before, self.after, self.regex = rel, before, after, regex
        self.original = None

    def __enter__(self):
        self.original = open(self.path, encoding="utf-8").read()
        if self.regex:
            new, n = re.subn(self.before, self.after, self.original, count=1)
        else:
            n = self.original.count(self.before)
            new = self.original.replace(self.before, self.after, 1)
        if not n:
            raise AssertionError(f"mutation target not found in {self.rel}: {self.before[:60]!r}")
        open(self.path, "w", encoding="utf-8").write(new)
        return self

    def __exit__(self, *exc):
        open(self.path, "w", encoding="utf-8").write(self.original)
        return False


class NewFile:
    """Drop a file in, remove it whatever happens."""

    def __init__(self, rel, content):
        self.path = os.path.join(HERE, rel)
        self.rel, self.content = rel, content

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        open(self.path, "w", encoding="utf-8").write(self.content)
        return self

    def __exit__(self, *exc):
        if os.path.exists(self.path):
            os.unlink(self.path)
        return False


class CheckCorpusIsNotVacuous(unittest.TestCase):
    """One case per assertion under test. Each proves the check fails on its own defect."""

    @classmethod
    def setUpClass(cls):
        rc, out = run_check()
        if rc != 0:
            raise unittest.SkipTest(f"check-corpus is not green before mutation:\n{out[-1500:]}")

    def assert_mutation_is_caught(self, mutation, check_name):
        """The contract: THAT check fails, named, with a message that identifies the problem.

        Asserting only a non-zero exit is not enough and the first version of this file proved it:
        neutralising every refusal in vcs.sh left its own check green and the run failed anyway,
        because a different suite caught the damage behaviourally. The harness reported a pass on a
        check that is vacuous — the same defect it exists to find, one level up. So the failure
        marker must sit on the line naming the check under test."""
        with mutation:
            rc, out = run_check()
        failed_lines = [l for l in out.split("\n") if l.lstrip().startswith("✗")]
        named = [l for l in failed_lines if check_name in l]
        self.assertTrue(
            named,
            f"`{check_name}` stayed green under its own defect.\n"
            f"Other checks that did fail: {failed_lines or 'none — the run was green'}")

    # --- the four already proven by hand in round 5 ------------------------------------------------
    def test_removing_a_human_gate_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".claude/agents/asdd-phase-2-discovery.md", "--human-gate", ""),
            "gates: 13 blocking, 9 requiring a human")

    def test_a_bare_python_invocation_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation(".claude/agents/asdd-phase-0-intake.md",
                     "python3 scripts/python/asdd_state.py", "python scripts/python/asdd_state.py"),
            "python3, not bare python")

    def test_dropping_the_change_discipline_reference_is_caught(self):
        self.assert_mutation_is_caught(
            Mutation("CLAUDE.md", "skills/engineering/change-discipline.md", "skills/engineering/xxx.md"),
            "change-discipline")

    def test_an_unindexed_adr_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("docs/adr/ADR-9999-mutation-probe.md",
                    "# ADR-9999 — probe\n\n**Status:** Accepted\n"),
            "adr-index")

    # --- the assertions this round repairs ---------------------------------------------------------
    def test_a_broken_internal_link_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("docs/mutation-probe.md",
                    "<!-- adopter-paths: probe -->\n\n# probe\n\n[dead](./does-not-exist.md)\n"),
            "links")

    def test_a_spec_with_a_bad_id_is_caught(self):
        self.assert_mutation_is_caught(
            NewFile("specs/api/mutation-probe.md",
                    "---\nid: NOT-A-SPEC-ID\nkind: spec\nstatus: approved\n---\n\n# probe\n"),
            "frontmatter")

    def test_a_neutralised_refusal_is_caught(self):
        """R5-T2. The check counted the string `refuse "` and passed while every refusal was a
        no-op — the single script that touches git was guarded by a word count."""
        self.assert_mutation_is_caught(
            Mutation("scripts/bash/vcs.sh",
                     'refuse() {\n    echo "REFUSED: $1" >&2',
                     'refuse() {\n    return 0\n    echo "REFUSED: $1" >&2'),
            "refuses merge, release, deploy, push")

    def test_a_productivity_ratio_is_caught_in_every_form(self):
        """R5-T3. The repaired regex caught only `N× faster` and lost the divided form the
        previous one caught."""
        forms = [
            "human-equivalent 320h ÷ agent wall-clock 2h = 160×",
            "We observed 160 times faster delivery.",
            "speedup ratio: 160",
            "The run was 160× faster.",
            "A 40x quicker pipeline than any benchmark.",
        ]
        for i, form in enumerate(forms):
            with self.subTest(form=form):
                self.assert_mutation_is_caught(
                    NewFile(f"docs/mutation-probe-ratio-{i}.md",
                            f"<!-- adopter-paths: probe -->\n\n# probe\n\n{form}\n"),
                    "speedup ratio")

    def test_a_restated_coverage_number_is_caught(self):
        """R5-T3. `Coverage MUST be 80% per ADR-0022.` passed, because citing the ADR exempted the
        line — and citing the ADR is exactly what a restated number would do."""
        self.assert_mutation_is_caught(
            Mutation("CLAUDE.md",
                     "- Unit coverage **MUST** be at or above the floor declared in ADR-0022",
                     "- Unit coverage **MUST** be 80% per ADR-0022"),
            "bare number")

    def test_a_stale_measurement_report_is_caught(self):
        """R5-T5. `--check` compared only section headings, so no number could fail it."""
        report = sorted(f for f in os.listdir(os.path.join(HERE, "docs", "sre"))
                        if f.startswith("corpus-metrics-") and f.endswith(".md"))[-1]
        self.assert_mutation_is_caught(
            Mutation(f"docs/sre/{report}", r"\| Markdown files \| \d+ \|",
                     "| Markdown files | 1 |", regex=True),
            "measurement report")

    def test_unmarked_unresolvable_evidence_is_caught(self):
        """R5-T4. The exemption list was widened until 145 of 146 evidence paths were exempt and
        the rule could no longer catch the case it was written for."""
        self.assert_mutation_is_caught(
            NewFile("specs/api/mutation-probe-evidence.md",
                    "---\nid: SPEC-API-099\nkind: spec\nstatus: implemented\n"
                    "verified_by:\n  - nowhere/does-not-exist.py\n---\n\n# probe\n"),
            "data-quality")


class TreeIsClean(unittest.TestCase):
    def test_no_mutation_leaked(self):
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                           cwd=HERE, timeout=60)
        # Untracked files are the author's business; a leak is a MODIFIED tracked file.
        modified = [l for l in r.stdout.split("\n") if l and not l.startswith("??")]
        self.assertEqual(modified, [], f"a mutation leaked into the tree:\n{chr(10).join(modified)}")


if __name__ == "__main__":
    unittest.main(verbosity=1)
