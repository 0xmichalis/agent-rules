import importlib.util
from contextlib import redirect_stderr
import io
from pathlib import Path
import tempfile
import unittest
import shutil
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "install_rules", Path(__file__).resolve().parents[1] / "scripts/install.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source checkout"
        self.home = self.root / "user home"
        self.source.mkdir()
        self.home.mkdir()
        (self.source / "AGENTS.md").write_text("# Shared rules\n")
        (self.source / "private-memory.md").write_text("Keep private\n")
        rules = self.source / ".claude/rules"
        rules.mkdir(parents=True)
        (rules / "rust.md").write_text("# Rust rules\n")

    def test_all_runners_share_content_and_install_does_not_depend_on_checkout(self):
        installer.install(self.source, self.home)
        shutil.rmtree(self.source)
        for entry in installer.ENTRIES:
            self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")
        self.assertIn(
            "# Shared rules\n", (self.home / ".hermes/SOUL.md").read_text()
        )
        self.assertFalse((self.home / ".config/opencode").exists())
        self.assertFalse((self.home / ".agents/agent-rules/private-memory.md").exists())
        self.assertEqual(
            (self.home / ".claude/rules/agent-rules/rust.md").read_text(),
            "# Rust rules\n",
        )

    def test_update_preserves_previous_files_and_unrelated_context(self):
        native = self.home / ".claude/CLAUDE.md"
        native.parent.mkdir()
        native.write_text("# Existing preferences\n")
        context = self.home / ".agents/CONTEXT.md"
        context.parent.mkdir()
        context.write_text("# Private project mapping\n")
        old_rules = self.home / ".claude/rules/agent-rules"
        old_rules.mkdir(parents=True)
        (old_rules / "legacy.md").write_text("# Old topic rules\n")
        backup = installer.install(self.source, self.home)
        self.assertEqual(
            (backup / ".claude/CLAUDE.md").read_text(), "# Existing preferences\n"
        )
        self.assertEqual(
            (backup / ".claude/rules/agent-rules/legacy.md").read_text(),
            "# Old topic rules\n",
        )
        (self.source / "AGENTS.md").write_text("# Updated rules\n")
        installer.install(self.source, self.home)
        installer.install(self.source, self.home)
        for entry in installer.ENTRIES:
            self.assertEqual((self.home / entry).read_text(), "# Updated rules\n")
        self.assertEqual(context.read_text(), "# Private project mapping\n")

    def test_hermes_updates_defaults_without_replacing_personality_or_profile_data(self):
        soul = self.home / ".hermes/SOUL.md"
        profile = self.home / ".hermes/profiles/work"
        profile.mkdir(parents=True)
        soul.write_text("# Personality\nKeep my preferred voice.\n")
        (profile / "SOUL.md").write_text("# Work personality\nKeep the work voice.\n")
        session = profile / "session.json"
        session.write_text('{"history": "preserve"}\n')
        empty_profile = self.home / ".hermes/profiles/other"
        empty_profile.mkdir()
        backup = installer.install(self.source, self.home)
        self.assertEqual(
            (backup / ".hermes/SOUL.md").read_text(),
            "# Personality\nKeep my preferred voice.\n",
        )
        (self.source / "AGENTS.md").write_text("# Updated rules\n")
        installer.install(self.source, self.home)
        installer.install(self.source, self.home)
        for path, personality in (
            (soul, "# Personality\nKeep my preferred voice.\n"),
            (profile / "SOUL.md", "# Work personality\nKeep the work voice.\n"),
            (empty_profile / "SOUL.md", ""),
        ):
            content = path.read_text()
            self.assertEqual(content.count("# Updated rules\n"), 1)
            self.assertNotIn("# Shared rules\n", content)
            self.assertTrue(content.endswith(personality))
        self.assertEqual(session.read_text(), '{"history": "preserve"}\n')

    def test_failed_hermes_update_restores_personality_and_previous_rules(self):
        soul = self.home / ".hermes/SOUL.md"
        profile = self.home / ".hermes/profiles/work"
        profile.mkdir(parents=True)
        soul.write_text("# Personality\n")
        installer.install(self.source, self.home)
        previous_soul = soul.read_text()
        previous_profile = (profile / "SOUL.md").read_text()
        (self.source / "AGENTS.md").write_text("# New rules\n")
        original = Path.rename
        failed = False

        def fail_profile_replacement(path, target):
            nonlocal failed
            if Path(target) == profile / "SOUL.md" and not failed:
                failed = True
                raise OSError("Simulated profile replacement failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_profile_replacement):
            with self.assertRaisesRegex(OSError, "Simulated profile"):
                installer.install(self.source, self.home)
        self.assertTrue(failed)
        self.assertEqual(soul.read_text(), previous_soul)
        self.assertEqual((profile / "SOUL.md").read_text(), previous_profile)
        for entry in installer.ENTRIES:
            self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")

    def test_incomplete_hermes_section_does_not_overwrite_personality_or_installation(self):
        installer.install(self.source, self.home)
        soul = self.home / ".hermes/SOUL.md"
        malformed = "# My personality\n<!-- agent-rules:start -->\nUnfinished edit\n"
        soul.write_text(malformed)
        (self.source / "AGENTS.md").write_text("# New rules\n")
        with self.assertRaisesRegex(ValueError, "managed section"):
            installer.install(self.source, self.home)
        self.assertEqual(soul.read_text(), malformed)
        for entry in installer.ENTRIES:
            self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")

    def test_failed_replacement_restores_working_installation(self):
        installer.install(self.source, self.home)
        (self.source / "AGENTS.md").write_text("# New rules\n")
        original = Path.rename

        def fail_second_entry(path, target):
            if path.name == "entry-1":
                raise OSError("Simulated replacement failure")
            return original(path, target)

        with patch.object(Path, "rename", fail_second_entry):
            with self.assertRaisesRegex(OSError, "Simulated"):
                installer.install(self.source, self.home)
        for entry in installer.ENTRIES:
            self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")

    def test_failed_rollback_restores_other_entries_and_preserves_original_error(self):
        installer.install(self.source, self.home)
        (self.source / "AGENTS.md").write_text("# New rules\n")
        original = Path.rename
        installation_error = OSError("Simulated replacement failure")

        def fail_installation_and_one_restore(path, target):
            if path.name == "entry-1":
                raise installation_error
            if path.name == "AGENTS.md" and path.parent.name == ".codex":
                if "backups" in path.parts:
                    raise OSError("Simulated rollback failure")
            return original(path, target)

        diagnostics = io.StringIO()
        with patch.object(Path, "rename", fail_installation_and_one_restore):
            with redirect_stderr(diagnostics):
                with self.assertRaises(OSError) as raised:
                    installer.install(self.source, self.home)

        self.assertIs(raised.exception, installation_error)
        self.assertEqual(
            (self.home / ".agents/agent-rules/AGENTS.md").read_text(),
            "# Shared rules\n",
        )
        for entry in installer.ENTRIES[1:]:
            self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")
        backups = list(
            (self.home / ".agents/backups/agent-rules").glob("*/.codex/AGENTS.md")
        )
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "# Shared rules\n")
        self.assertIn("Simulated rollback failure", diagnostics.getvalue())
        self.assertIn(str(backups[0].parents[1]), diagnostics.getvalue())


if __name__ == "__main__":
    unittest.main()
