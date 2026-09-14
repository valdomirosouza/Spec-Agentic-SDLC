#!/usr/bin/env python3
"""Tests for scripts/python/check_changelog.py (#77). stdlib only."""
import os
import re
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


class NextVersion(unittest.TestCase):
    """R7-T5. A rule written ("the version of record follows SemVer") with nothing that acts on it."""

    def check(self, changelog, version="1.0.0"):
        import contextlib, io, tempfile
        real_root = cc.ROOT
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, cc.CHANGELOG), "w", encoding="utf-8") as fh:
                fh.write(changelog)
            with open(os.path.join(d, cc.VERSION_FILE), "w", encoding="utf-8") as fh:
                fh.write(version + "\n")
            cc.ROOT = d
            out, err = io.StringIO(), io.StringIO()
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    rc = cc.main(["--version", "--quiet"])
            finally:
                cc.ROOT = real_root
            return rc, out.getvalue() + err.getvalue()

    def test_a_breaking_label_with_nothing_published_broken_fails(self):
        """R8-T5. The case this rule exists for, and it was my own claim: asdd_state.py arrived
        after 1.0.0, so nobody on that release holds a v1 file and the schema change breaks no
        published contract. The label, and the 2.0.0 it forced, overstated the impact."""
        rc, out = self.check(
            f"{cc.UNRELEASED}\n\n- **BREAKING: the schema changed**\n")
        self.assertEqual(rc, 1)
        self.assertIn("no contract published at the last release changed", out)

    def test_prose_describing_a_claim_is_not_a_claim(self):
        """Scanning for the bare word fired on the lines that explain this rule. A checker that
        cannot tell a description from an assertion makes its own documentation unpublishable."""
        rc, _ = self.check(
            f"{cc.UNRELEASED}\n\n- the gate ties a BREAKING entry to the version it forces\n")
        self.assertEqual(rc, 0)

    def test_no_breaking_needs_no_declaration(self):
        rc, _ = self.check(f"{cc.UNRELEASED}\n\n- a quiet fix\n")
        self.assertEqual(rc, 0)

    def test_a_declared_version_behind_the_current_one_fails(self):
        rc, out = self.check(f"{cc.UNRELEASED}\n\n> **Next version:** 0.9.0\n\n- a fix\n")
        self.assertEqual(rc, 1)
        self.assertIn("not ahead of", out)

    def test_breaking_in_an_older_release_does_not_count(self):
        """The block stops at the next release heading, so a break shipped long ago cannot keep
        demanding a bump for ever."""
        rc, _ = self.check(
            f"{cc.UNRELEASED}\n\n- a fix\n\n## [1.0.0]\n\n- **BREAKING: old news**\n")
        self.assertEqual(rc, 0)

    def test_a_contract_absent_at_the_release_cannot_break_anyone(self):
        breaks, notes = cc.derived_breaks()
        self.assertEqual(breaks, [], "nothing published in 1.0.0 has changed value")
        self.assertTrue(any("did not exist at the last release" in n for n in notes))


class DerivedContracts(unittest.TestCase):
    """R9-T3. The published registry is machine-readable data an adopter can consume, and it gained
    a field this session with nothing to record the change. It carries a version now."""

    def test_the_registry_is_a_tracked_contract(self):
        self.assertIn("scripts/python/build_spec_registry.py", [c[0] for c in cc.CONTRACTS])

    def test_every_tracked_contract_declares_a_version_today(self):
        for path, pattern in cc.CONTRACTS:
            text = open(os.path.join(cc.ROOT, path), encoding="utf-8").read()
            self.assertRegex(text, re.compile(pattern, re.M), path)

    def test_a_changed_contract_value_is_a_derived_break(self):
        """The live repository cannot exercise this: both contracts postdate release 1.0.0, so
        nothing held against them can break. The comparison itself is what is proved here."""
        real_at, real_commit = cc._at, cc.release_commit
        cc.release_commit = lambda: "pretend-release"
        cc._at = lambda commit, path: 'SCHEMA_VERSION = "older_value"\n'
        try:
            breaks, _ = cc.derived_breaks()
        finally:
            cc._at, cc.release_commit = real_at, real_commit
        self.assertEqual(len(breaks), len(cc.CONTRACTS))
        self.assertIn("older_value", breaks[0])

    def test_an_unchanged_contract_value_is_not_a_break(self):
        real_at, real_commit = cc._at, cc.release_commit
        cc.release_commit = lambda: "pretend-release"
        cc._at = lambda commit, path: open(os.path.join(cc.ROOT, path), encoding="utf-8").read()
        try:
            breaks, _ = cc.derived_breaks()
        finally:
            cc._at, cc.release_commit = real_at, real_commit
        self.assertEqual(breaks, [])


class LiveTree(unittest.TestCase):
    def test_it_runs_against_this_repository(self):
        r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True,
                           cwd=HERE, timeout=120)
        self.assertIn(r.returncode, (0, 1), r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
