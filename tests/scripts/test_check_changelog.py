#!/usr/bin/env python3
"""Tests for scripts/python/check_changelog.py (#77). stdlib only."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(HERE, "scripts", "python", "check_changelog.py")
sys.path.insert(0, os.path.join(HERE, "scripts", "python"))
import check_changelog as cc  # noqa: E402


class Scope(unittest.TestCase):
    """What owes an entry. Prose describing unchanged behaviour does not, which is why docs/ and
    specs/ are absent; things that execute or bind do."""

    def test_executables_and_contracts_are_watched(self):
        for p in ("scripts/python/x.py", ".github/workflows/x.yml", ".claude/hooks/x.py",
                  "memory/constitution.md", "CLAUDE.md"):
            self.assertTrue(p.startswith(cc.WATCHED), p)

    def test_prose_is_not_watched(self):
        for p in ("docs/adr/ADR-0001.md", "specs/api/x.md", "README.md"):
            self.assertFalse(p.startswith(cc.WATCHED), p)

    def test_generated_artefacts_are_exempt(self):
        """They are rewritten on nearly every run as a side effect of measuring. An entry for each
        would be noise, and noise teaches people to ignore the gate."""
        for p in ("docs/sre/corpus-metrics-2026-09-13.md", "docs/governance/spec-registry.json"):
            self.assertTrue(p.startswith(cc.EXEMPT), p)


class Behaviour(unittest.TestCase):
    def run_with(self, changed, changelog_text, waiver=None):
        real_changed, real_root = cc.changed_paths, cc.ROOT
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, cc.CHANGELOG), "w", encoding="utf-8") as fh:
                fh.write(changelog_text)
            cc.ROOT = d
            cc.changed_paths = lambda: set(changed)
            old = os.environ.get("CHANGELOG_WAIVER")
            if waiver is not None:
                os.environ["CHANGELOG_WAIVER"] = waiver
            try:
                return cc.main(["--quiet"])
            finally:
                cc.changed_paths, cc.ROOT = real_changed, real_root
                if waiver is not None:
                    if old is None:
                        os.environ.pop("CHANGELOG_WAIVER", None)
                    else:
                        os.environ["CHANGELOG_WAIVER"] = old

    def test_a_script_change_without_an_entry_fails(self):
        self.assertEqual(self.run_with({"scripts/python/x.py"}, cc.UNRELEASED), 1)

    def test_a_script_change_with_an_entry_passes(self):
        self.assertEqual(
            self.run_with({"scripts/python/x.py", cc.CHANGELOG}, cc.UNRELEASED), 0)

    def test_prose_alone_owes_nothing(self):
        self.assertEqual(self.run_with({"docs/adr/ADR-0001.md"}, cc.UNRELEASED), 0)

    def test_a_generated_report_alone_owes_nothing(self):
        self.assertEqual(
            self.run_with({"docs/sre/corpus-metrics-2026-09-13.md"}, cc.UNRELEASED), 0)

    def test_a_changelog_with_no_unreleased_section_fails_on_a_clean_tree(self):
        """The invariant is unconditional on purpose. Checking it only when something was owing made
        it depend on the working tree, so it could not be proved on a clean one."""
        self.assertEqual(self.run_with(set(), "# Changelog\n"), 1)

    def test_the_waiver_lets_a_change_through_and_is_never_silent(self):
        self.assertEqual(
            self.run_with({"scripts/python/x.py"}, cc.UNRELEASED, waiver="release prep"), 0)

    def test_an_empty_waiver_is_not_a_waiver(self):
        self.assertEqual(
            self.run_with({"scripts/python/x.py"}, cc.UNRELEASED, waiver="   "), 1)


class LiveTree(unittest.TestCase):
    def test_it_runs_against_this_repository(self):
        r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True,
                           cwd=HERE, timeout=120)
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
