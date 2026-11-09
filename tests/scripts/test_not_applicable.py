#!/usr/bin/env python3
"""Tests for scripts/python/not_applicable.py, declared n/a checks (ADR-0098). stdlib only."""
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import not_applicable as na  # noqa: E402

TODAY = datetime.date(2026, 11, 9)
VERIFIER = 'result "links" ok\nresult "throttled responses name the caller\'s budget" ok\nresult "verify-high-risk-guard" ok\n'


def entry(check="links", reason="no docs site", owner="platform-team", review_by="2027-01-31"):
    return (f'  - check: "{check}"\n    reason: "{reason}"\n    owner: "{owner}"\n'
            f'    review_by: "{review_by}"\n')


class NotApplicable(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "docs", "governance"))
        os.makedirs(os.path.join(self.root, "scripts", "bash"))
        open(os.path.join(self.root, na.VERIFIER), "w").write(VERIFIER)

    def tearDown(self):
        shutil.rmtree(self.root)

    def matrix(self, body):
        open(os.path.join(self.root, na.MATRIX), "w").write(f"version: 1\n{body}\nregulatory_scope:\n  sox:\n    in_scope: false\n")

    def states(self):
        return [(s, e.get("check")) for s, _, e in na.declarations(self.root, TODAY)[1]]

    def test_an_empty_list_declares_nothing(self):
        self.matrix("adoption_profile: service\nnot_applicable: []\n")
        self.assertEqual(na.declarations(self.root, TODAY), ("service", []))
        self.assertEqual(na.problems(self.root, TODAY), [])

    def test_an_absent_matrix_declares_nothing(self):
        self.assertEqual(na.declarations(self.root, TODAY), (None, []))

    def test_a_complete_declaration_is_active(self):
        self.matrix("adoption_profile: batch-data\nnot_applicable:\n" + entry())
        self.assertEqual(self.states(), [("active", "links")])
        self.assertEqual(na.problems(self.root, TODAY), [])

    def test_an_apostrophe_in_a_check_name_survives_quoting(self):
        self.matrix("not_applicable:\n" + entry(check="throttled responses name the caller's budget"))
        self.assertEqual(self.states(), [("active", "throttled responses name the caller's budget")])

    def test_a_declaration_past_review_by_expires(self):
        """ADR-0098 §4: an n/a must not become the permanent state it replaced."""
        self.matrix("not_applicable:\n" + entry(review_by="2026-11-08"))
        self.assertEqual(self.states(), [("expired", "links")])

    def test_a_protected_check_is_refused(self):
        self.matrix("not_applicable:\n" + entry(check="verify-high-risk-guard"))
        self.assertEqual(self.states(), [("refused", "verify-high-risk-guard")])
        self.assertTrue(any("enforces Article V" in p for p in na.problems(self.root, TODAY)))

    def test_every_refused_name_is_a_check_the_verifier_prints(self):
        """A refused name that matches nothing protects nothing: a renamed check would slip out."""
        printed = na.check_names(HERE)
        self.assertEqual(sorted(set(na.REFUSED) - printed), [])

    def test_an_unknown_check_name_is_invalid(self):
        """A typo would otherwise silence nothing and still look like a declaration."""
        self.matrix("not_applicable:\n" + entry(check="lnks"))
        self.assertEqual(self.states(), [("invalid", "lnks")])

    def test_a_missing_field_is_invalid(self):
        self.matrix('not_applicable:\n  - check: "links"\n    reason: "x"\n    review_by: "2027-01-31"\n')
        self.assertTrue(any("missing owner" in p for p in na.problems(self.root, TODAY)))

    def test_a_bad_date_is_invalid(self):
        self.matrix("not_applicable:\n" + entry(review_by="2027-02-30"))
        self.assertEqual(self.states(), [("invalid", "links")])

    def test_an_unknown_profile_is_a_problem(self):
        self.matrix("adoption_profile: serverless\nnot_applicable: []\n")
        self.assertTrue(any("serverless" in p for p in na.problems(self.root, TODAY)))

    def test_the_corpus_own_matrix_is_valid(self):
        self.assertEqual(na.problems(HERE), [])

    def test_check_exits_nonzero_on_a_refused_declaration(self):
        self.matrix("not_applicable:\n" + entry(check="verify-high-risk-guard"))
        r = subprocess.run([sys.executable, os.path.join(HERE, "scripts", "python", "not_applicable.py"), "--check"],
                           cwd=self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("refused", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
