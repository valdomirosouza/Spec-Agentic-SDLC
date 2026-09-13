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


class Ratchet(unittest.TestCase):
    def run_check(self, baseline):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "baseline.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(baseline, fh)
            env = dict(os.environ)
            code = (f"import sys; sys.argv=['x','--check','--quiet'];"
                    f"sys.path.insert(0,{os.path.join(HERE, 'scripts', 'python')!r});"
                    f"import mutation_coverage as m; m.BASELINE={path!r}; sys.exit(m.main())")
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               cwd=HERE, env=env, timeout=120)
            return r.returncode, r.stdout + r.stderr

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
