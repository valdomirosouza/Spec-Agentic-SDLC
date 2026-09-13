#!/usr/bin/env python3
"""Tests for scripts/python/mutation_coverage.py (#75). stdlib only."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "mutation_coverage.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import mutation_coverage as mc  # noqa: E402


class Parsing(unittest.TestCase):
    def test_it_reads_the_real_check_names(self):
        names = mc.named_checks()
        self.assertGreater(len(names), 30)
        self.assertIn("links", names)

    def test_it_reads_the_proofs_from_the_syntax_tree(self):
        """A regular expression loose enough to reach the second argument past a multi-line first
        one also matches unrelated strings in the same call, so this parses the tree instead."""
        proofs = mc.proved_names()
        self.assertIn("links", proofs)
        self.assertNotIn("", proofs)

    def test_a_mutation_naming_nothing_is_an_orphan_not_silent(self):
        real = mc.proved_names
        mc.proved_names = lambda: sorted(set(real()) | {"no such check anywhere"})
        try:
            c = mc.coverage()
            self.assertIn("no such check anywhere", c["orphan_mutations"])
        finally:
            mc.proved_names = real


class Vacuity(unittest.TestCase):
    """R8-T1. The cheap guard: a name that can only print `ok` cannot fail the build."""

    def test_the_live_verifier_has_no_check_that_cannot_fail(self):
        self.assertEqual(mc.vacuity_problems(), [])

    def test_a_check_with_only_an_ok_site_is_reported(self):
        real = mc.call_sites
        mc.call_sites = lambda: {"a real check": {"ok", "fail"}, "neutered": {"ok"}}
        try:
            problems = mc.vacuity_problems()
        finally:
            mc.call_sites = real
        self.assertEqual(len(problems), 1)
        self.assertIn("neutered", problems[0])

    def test_a_note_only_check_is_still_reported(self):
        """`note` is visible and does not fail the build, so a check that can only note is as
        unable to stop anything as one that can only pass."""
        real = mc.call_sites
        mc.call_sites = lambda: {"alerts only": {"ok", "note"}}
        try:
            self.assertEqual(len(mc.vacuity_problems()), 1)
        finally:
            mc.call_sites = real

    def test_an_unclassifiable_status_is_reported_not_assumed_fine(self):
        real = mc.call_sites
        mc.call_sites = lambda: {"computed status": set()}
        try:
            self.assertIn("cannot be classified", mc.vacuity_problems()[0])
        finally:
            mc.call_sites = real

    def test_every_name_resolves_to_one_set_of_call_sites(self):
        """Two checks printed a different name from their ok and fail branches, so the name a
        reader saw passing was not the name that appeared on failure, and the count included
        phantoms (R8-T1)."""
        self.assertEqual(len(mc.call_sites()), len(mc.named_checks()))


class Ratchet(unittest.TestCase):
    def run_check(self, baseline):
        """In-process, so a monkeypatched `named_checks` is visible. An earlier version shelled out
        and could only vary the baseline, never the live corpus."""
        import contextlib, io
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "baseline.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(baseline, fh)
            real = mc.BASELINE
            mc.BASELINE = path
            out, err = io.StringIO(), io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    rc = mc.main(["--check", "--quiet"])
            finally:
                mc.BASELINE = real
            return rc, out.getvalue() + err.getvalue()

    def test_current_coverage_satisfies_the_committed_baseline(self):
        r = subprocess.run([sys.executable, SCRIPT, "--check"], capture_output=True, text=True,
                           cwd=HERE, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fewer_proofs_than_the_baseline_fails(self):
        c = mc.coverage()
        rc, out = self.run_check({"named": c["named"], "proved": c["proved"] + 1})
        self.assertEqual(rc, 1)
        self.assertIn("fell", out)

    def test_a_new_check_without_a_proof_fails_even_though_the_count_did_not_fall(self):
        """The count alone cannot see this: adding an unproved check leaves `proved` untouched.
        The ratio is what catches it, and it is the case the ratchet exists for."""
        c = mc.coverage()
        rc, out = self.run_check({"named": c["named"] - 1, "proved": c["proved"]})
        self.assertEqual(rc, 1)
        self.assertIn("without a mutation", out)

    def test_deleting_an_unproved_check_fails_even_though_the_ratio_improved(self):
        """R7-T1. The ratio was the only guard, and a ratio rises when its denominator shrinks:
        deleting twenty unproved checks moved coverage from 32% to 52% and the gate approved it. A
        gate built to protect verification had made removing verification the cheapest way to
        satisfy it."""
        c = mc.coverage()
        names = mc.named_checks()
        surviving = [n for n in names if n not in mc.proved_names()]
        self.assertTrue(surviving, "expected at least one unproved check to pretend to delete")
        doomed = surviving[:5]
        baseline = {"named": c["named"], "proved": c["proved"], "checks": names}
        real = mc.named_checks
        mc.named_checks = lambda: [n for n in names if n not in doomed]
        try:
            rc, out = self.run_check(baseline)
        finally:
            mc.named_checks = real
        self.assertEqual(rc, 1, "deleting checks must not be a way to pass")
        self.assertIn("no longer in check-corpus.sh", out)
        for d in doomed:
            self.assertIn(d, out, "the failure must name the check that went missing")

    def test_the_deletion_guard_survives_a_baseline_written_before_it_existed(self):
        """An older baseline has no `checks` key. It must not crash, and it must not pretend to
        guard something it cannot see."""
        c = mc.coverage()
        rc, _ = self.run_check({"named": c["named"], "proved": c["proved"]})
        self.assertEqual(rc, 0)

    def test_a_missing_baseline_fails_rather_than_passing_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            code = (f"import sys; sys.argv=['x','--check'];"
                    f"sys.path.insert(0,{os.path.join(HERE, 'scripts', 'python')!r});"
                    f"import mutation_coverage as m;"
                    f"m.BASELINE={os.path.join(d, 'absent.json')!r}; sys.exit(m.main())")
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               cwd=HERE, timeout=120)
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
