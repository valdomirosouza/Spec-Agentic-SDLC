#!/usr/bin/env python3
"""Tests for scripts/python/check_adr_index.py, check-corpus.sh C3 (ADR-0097). stdlib only."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import check_adr_index as c3  # noqa: E402


class AdrIndex(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "docs", "adr"))
        self.links = []

    def tearDown(self):
        shutil.rmtree(self.root)

    def adr(self, n, slug="decision", status="Accepted", indexed=True):
        name = f"ADR-{n:04d}-{slug}.md"
        open(os.path.join(self.root, "docs", "adr", name), "w").write(
            f"# ADR-{n:04d} — {slug}\n\n**Status:** {status}\n")
        if indexed:
            self.links.append(name)
        return name

    def run_check(self):
        open(os.path.join(self.root, "docs", "adr", "README.md"), "w").write(
            "\n".join(f"| [{n[:8]}]({n}) | x |" for n in self.links) + "\n")
        return c3.problems(self.root)

    def test_contiguous_corpus_range_passes(self):
        for n in (1, 2, 3):
            self.adr(n)
        self.assertEqual(self.run_check(), (3, []))

    def test_a_gap_in_the_corpus_range_fails(self):
        self.adr(1); self.adr(3)
        count, bad = self.run_check()
        self.assertTrue(any("corpus range: [2]" in b for b in bad), bad)

    def test_an_adopter_range_from_1000_passes_beside_the_corpus(self):
        """The adopter's numbers do not continue the corpus's, and that is not a gap."""
        for n in (1, 2, 1000, 1001):
            self.adr(n)
        self.assertEqual(self.run_check(), (4, []))

    def test_an_adopter_range_that_skips_1000_fails(self):
        self.adr(1); self.adr(1001)
        count, bad = self.run_check()
        self.assertTrue(any("adopter range (ADR-1000+): [1000]" in b for b in bad), bad)

    def test_a_plain_duplicate_fails(self):
        self.adr(1); self.adr(1, "other")
        count, bad = self.run_check()
        self.assertTrue(any(b.startswith("duplicate ADR-0001") for b in bad), bad)

    def test_a_collision_restated_in_the_adopter_range_passes(self):
        """ADR-0097 §3: the colliding local file stays, superseded by its 1000+ restatement."""
        self.adr(1); self.adr(1, "local", status="Superseded by ADR-1000"); self.adr(1000, "local")
        self.assertEqual(self.run_check(), (3, []))

    def test_the_table_status_style_is_read_too(self):
        self.adr(1); self.adr(1000, "local")
        name = self.adr(1, "local", indexed=True)
        open(os.path.join(self.root, "docs", "adr", name), "w").write(
            "# ADR-0001\n\n| **Status** | Superseded by ADR-1000 |\n")
        self.assertEqual(self.run_check(), (3, []))

    def test_a_restatement_whose_successor_is_missing_fails(self):
        self.adr(1); self.adr(1, "local", status="Superseded by ADR-1000")
        count, bad = self.run_check()
        self.assertTrue(any("ADR-1000, which does not exist" in b for b in bad), bad)

    def test_a_duplicate_superseded_by_a_corpus_adr_still_fails(self):
        """Only a restatement in the adopter range excuses a duplicate."""
        self.adr(1); self.adr(2); self.adr(1, "local", status="Superseded by ADR-0002")
        count, bad = self.run_check()
        self.assertTrue(any(b.startswith("duplicate ADR-0001") for b in bad), bad)

    def test_a_duplicate_in_the_adopter_range_fails(self):
        self.adr(1000); self.adr(1000, "other", status="Superseded by ADR-1001"); self.adr(1001)
        count, bad = self.run_check()
        self.assertTrue(any(b.startswith("duplicate ADR-1000") for b in bad), bad)

    def test_an_unindexed_adr_and_a_dead_link_fail(self):
        self.adr(1); self.adr(2, indexed=False)
        self.links.append("ADR-0003-gone.md")
        count, bad = self.run_check()
        self.assertIn("not in docs/adr/README.md: ADR-0002-decision.md", bad)
        self.assertIn("index links a missing file: ADR-0003-gone.md", bad)

    def test_no_adrs_does_not_apply(self):
        self.assertIsNone(c3.problems(self.root))


if __name__ == "__main__":
    unittest.main(verbosity=1)
