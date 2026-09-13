#!/usr/bin/env python3
"""Tests for scripts/python/check_control_matrix.py (#43). stdlib only."""
import os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "check_control_matrix.py")

VALID = """standard: Test Standard
version: 1.0
controls:
  - id: T-1
    control: A thing is done.
    implemented_by:
      - memory/constitution.md
      - adopter:src/whatever.py
    verified_by:
      - "ci:Unit Tests"
    owner: Tech Lead
    status: implemented
  - id: T-2
    control: Another thing.
    implemented_by:
      - memory/constitution.md
    owner: Security Lead
    status: partial
    gap: >-
      A named gap that spans
      two lines.
  - id: T-3
    control: Not applicable here.
    implemented_by: []
    owner: DPO
    status: n/a
    justification: Does not apply because there is no such surface.
"""


def run(text=None, path=None):
    d = tempfile.mkdtemp()
    rel = "m.yaml"
    p = path or os.path.join(d, rel)
    if text is not None:
        open(p, "w").write(text)
    r = subprocess.run([sys.executable, SCRIPT, "--quiet", os.path.relpath(p, HERE)],
                       capture_output=True, text=True, cwd=HERE, timeout=60)
    return r.returncode, r.stdout + r.stderr, d


class ControlMatrixValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.join(HERE, "_tmp_matrix_test")
        os.makedirs(self.tmp, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def check(self, text):
        p = os.path.join(self.tmp, "m.yaml")
        open(p, "w").write(text)
        r = subprocess.run([sys.executable, SCRIPT, "--quiet", os.path.relpath(p, HERE)],
                           capture_output=True, text=True, cwd=HERE, timeout=60)
        return r.returncode, r.stdout + r.stderr

    def test_valid_matrix_passes(self):
        rc, out = self.check(VALID)
        self.assertEqual(rc, 0, out)

    def test_missing_owner_fails(self):
        rc, out = self.check(VALID.replace("    owner: Tech Lead\n", ""))
        self.assertEqual(rc, 1); self.assertIn("has no owner", out)

    def test_missing_status_fails(self):
        rc, out = self.check(VALID.replace("    status: implemented\n", ""))
        self.assertEqual(rc, 1); self.assertIn("has no status", out)

    def test_unknown_status_fails(self):
        rc, out = self.check(VALID.replace("status: implemented", "status: mostly-ok"))
        self.assertEqual(rc, 1); self.assertIn("not in", out)

    def test_na_without_justification_fails(self):
        rc, out = self.check(VALID.replace("    justification: Does not apply because there is no such surface.\n", ""))
        self.assertEqual(rc, 1); self.assertIn("n/a without a justification", out)

    def test_partial_without_gap_fails(self):
        rc, out = self.check(VALID.replace("    gap: >-\n      A named gap that spans\n      two lines.\n", ""))
        self.assertEqual(rc, 1); self.assertIn("partial without a gap", out)

    def test_duplicate_id_fails(self):
        rc, out = self.check(VALID.replace("  - id: T-2", "  - id: T-1"))
        self.assertEqual(rc, 1); self.assertIn("duplicate id", out)

    def test_nonexistent_corpus_path_fails(self):
        rc, out = self.check(VALID.replace("memory/constitution.md", "memory/does-not-exist.md"))
        self.assertEqual(rc, 1); self.assertIn("does not exist", out)

    def test_adopter_prefixed_path_is_not_checked(self):
        rc, out = self.check(VALID.replace("adopter:src/whatever.py", "adopter:src/nothing/here.py"))
        self.assertEqual(rc, 0, out)

    def test_ci_job_is_not_a_path(self):
        rc, out = self.check(VALID.replace('"ci:Unit Tests"', '"ci:Some Job That Is Not A File"'))
        self.assertEqual(rc, 0, out)

    def test_planned_marker_is_reported_not_failed(self):
        rc, out = self.check(VALID.replace("      - adopter:src/whatever.py", "      - planned:#99:docs/future.md"))
        self.assertEqual(rc, 0, out); self.assertIn("planned issue #99", out)

    def test_missing_top_level_keys_fail(self):
        rc, out = self.check(VALID.replace("standard: Test Standard\n", ""))
        self.assertEqual(rc, 1); self.assertIn("missing top-level", out)

    def test_evidence_required_unless_na_or_prohibited(self):
        rc, out = self.check(VALID.replace("    implemented_by:\n      - memory/constitution.md\n      - adopter:src/whatever.py\n    verified_by:\n      - \"ci:Unit Tests\"\n", ""))
        self.assertEqual(rc, 1); self.assertIn("no evidence", out)

    def test_real_matrices_are_valid(self):
        r = subprocess.run([sys.executable, SCRIPT, "--quiet"], capture_output=True, text=True, cwd=HERE, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
