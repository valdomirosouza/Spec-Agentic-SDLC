#!/usr/bin/env python3
"""Tests for scripts/python/check_open_items.py (#78). stdlib only."""
import datetime
import os
import subprocess
import sys
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "check_open_items.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import check_open_items as oi  # noqa: E402


class Vocabulary(unittest.TestCase):
    def test_an_iso_date_is_a_date(self):
        kind, due = oi.classify("2026-12-13")
        self.assertEqual(kind, "dated")
        self.assertEqual(due, datetime.date(2026, 12, 13))

    def test_a_declared_trigger_is_accepted_and_never_expires(self):
        """Conditioning an item on a real event is often more honest than a date someone made up.
        The defect was having no way to tell the two apart."""
        self.assertEqual(oi.classify("on-event: before synthetic data is used")[0], "on-event")

    def test_a_trigger_written_as_prose_is_unmarked(self):
        """`Next quarterly review` is what thirty rows said. Nothing convenes that review, and an
        item phrased that way can never come due."""
        for prose in ("Next quarterly review", "Before pursuing certification", "First deployment"):
            self.assertEqual(oi.classify(prose)[0], "unmarked", prose)

    def test_an_empty_trigger_is_not_a_trigger(self):
        self.assertEqual(oi.classify("on-event:")[0], "unmarked")

    def test_table_furniture_and_resolved_rows_are_not_items(self):
        self.assertEqual(oi.classify("Suggested target")[0], "furniture")
        self.assertEqual(oi.classify("✅")[0], "done")


class LiveCorpus(unittest.TestCase):
    def test_no_open_item_is_unmarked(self):
        buckets, _ = oi.audit()
        self.assertEqual([f"{r}:{n}" for r, n, _ in buckets["unmarked"]], [],
                         "every open item must carry a date or a declared trigger")

    def test_nothing_is_overdue_and_the_check_agrees(self):
        _, overdue = oi.audit()
        self.assertEqual([f"{r}:{n}" for r, n, _, _ in overdue], [])
        r = subprocess.run([sys.executable, SCRIPT, "--check"], capture_output=True, text=True,
                           cwd=HERE, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_corpus_actually_has_open_items_to_check(self):
        """Guards against the whole thing passing because the parser stopped finding anything."""
        buckets, _ = oi.audit()
        self.assertGreater(len(buckets["dated"]) + len(buckets["on-event"]), 20)

    def test_the_scope_baseline_names_the_table_that_vanished(self):
        """R8-T3. The floors were constants nobody raised: every item added widened the slack and
        nothing gave it back. A count also cannot say WHICH table disappeared (the lesson of #79)."""
        buckets, _ = oi.audit()
        base = oi.read_baseline()
        self.assertIsNotNone(base, "a committed baseline is what makes this a ratchet")
        real = oi._TABLES
        oi._TABLES = set(list(real)[:-1])
        try:
            problems = oi.scope_problems(buckets)
        finally:
            oi._TABLES = real
        self.assertTrue(problems)
        self.assertIn("are gone", problems[0])

    def test_the_live_scope_satisfies_the_committed_baseline(self):
        buckets, _ = oi.audit()
        self.assertEqual(oi.scope_problems(buckets), [])

    def test_a_missing_baseline_fails_rather_than_passing(self):
        real = oi.BASELINE
        oi.BASELINE = os.path.join(HERE, "tests", ".absent-baseline.json")
        try:
            buckets, _ = oi.audit()
            self.assertTrue(oi.scope_problems(buckets))
        finally:
            oi.BASELINE = real

    def test_no_date_carries_more_items_than_the_limit(self):
        """R7-T4. Converting eleven quarterly deferrals to the real quarterly date put every one on
        the same day: one morning the build turns red for everyone and the cheapest way out is to
        push eleven dates without reading a single item."""
        import collections
        buckets, _ = oi.audit()
        crowded = {d: n for d, n in collections.Counter(c for _, _, c in buckets["dated"]).items()
                   if n > oi.MAX_PER_DATE}
        self.assertEqual(crowded, {}, "deadlines must arrive in batches a reviewer can read")

    def test_the_deadlines_are_spread_over_more_than_one_day(self):
        buckets, _ = oi.audit()
        self.assertGreater(len({c for _, _, c in buckets["dated"]}), 2,
                           "a single shared date is the wall this guards against")

    def test_a_date_in_the_past_is_overdue(self):
        buckets, _ = oi.audit(today=datetime.date(2099, 1, 1))
        _, overdue = oi.audit(today=datetime.date(2099, 1, 1))
        self.assertTrue(overdue, "every dated item is in the past when read from 2099")
        self.assertEqual(len(overdue), len(buckets["dated"]))


if __name__ == "__main__":
    unittest.main(verbosity=1)
