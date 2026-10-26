import importlib.util
from contextlib import redirect_stderr
import io
import os
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
        environment = patch.dict(os.environ, {"HERMES_HOME": ""})
        environment.start()
        self.addCleanup(environment.stop)
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
        (empty_profile / "config.yaml").write_text("{}\n")
        ignored = self.home / ".hermes/profiles/logs"
        ignored.mkdir()
        (ignored / "agent.log").write_text("Keep the log\n")
        deleted = self.home / ".hermes/profiles/deleted"
        deleted.mkdir()
        (deleted / "config.yaml").write_text("{}\n")
        tombstones = self.home / ".hermes/profiles/.deleted"
        tombstones.mkdir()
        (tombstones / "deleted").touch()
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
        self.assertFalse((ignored / "SOUL.md").exists())
        self.assertFalse((deleted / "SOUL.md").exists())
        self.assertEqual((ignored / "agent.log").read_text(), "Keep the log\n")

    def test_custom_hermes_home_outside_user_home_has_updates_and_backups(self):
        custom = self.root / "external Hermes home"
        custom.mkdir()
        (custom / "SOUL.md").write_text("# External personality\n")
        profile = custom / "profiles/work"
        profile.mkdir(parents=True)
        (profile / "config.yaml").write_text("{}\n")
        with patch.dict(os.environ, {"HERMES_HOME": str(custom)}):
            backup = installer.install(self.source, self.home)
            self.assertIn("# Shared rules\n", (custom / "SOUL.md").read_text())
            self.assertIn("# Shared rules\n", (profile / "SOUL.md").read_text())
            self.assertEqual(
                (backup / "hermes-home/SOUL.md").read_text(),
                "# External personality\n",
            )
            (self.source / "AGENTS.md").write_text("# Updated rules\n")
            installer.install(self.source, self.home)
        self.assertFalse((self.home / ".hermes").exists())
        content = (custom / "SOUL.md").read_text()
        self.assertIn("# Updated rules\n", content)
        self.assertNotIn("# Shared rules\n", content)
        self.assertTrue(content.endswith("# External personality\n"))
        self.assertEqual((profile / "config.yaml").read_text(), "{}\n")

    def test_custom_hermes_home_replacement_failure_restores_external_file(self):
        custom = self.root / "external Hermes home"
        custom.mkdir()
        soul = custom / "SOUL.md"
        soul.write_text("# External personality\n")
        original = Path.rename
        failed = False

        def fail_custom_replacement(path, target):
            nonlocal failed
            if Path(target) == soul and not failed:
                failed = True
                raise OSError("Simulated external replacement failure")
            return original(path, target)

        with patch.dict(os.environ, {"HERMES_HOME": str(custom)}):
            with patch.object(Path, "rename", fail_custom_replacement):
                with self.assertRaisesRegex(OSError, "Simulated external"):
                    installer.install(self.source, self.home)
        self.assertTrue(failed)
        self.assertEqual(soul.read_text(), "# External personality\n")
        self.assertFalse((self.home / ".agents/agent-rules").exists())

    def test_upgrade_archives_only_the_owned_legacy_opencode_link(self):
        legacy = self.home / ".config/opencode/AGENTS.md"
        legacy.parent.mkdir(parents=True)
        legacy.symlink_to(self.home / ".agents/agent-rules/AGENTS.md")
        settings = legacy.parent / "settings.json"
        settings.write_text('{"keep": true}\n')
        backup = installer.install(self.source, self.home)
        self.assertFalse(legacy.is_symlink())
        self.assertFalse(legacy.exists())
        self.assertTrue((backup / ".config/opencode/AGENTS.md").is_symlink())
        self.assertEqual(settings.read_text(), '{"keep": true}\n')
        legacy.write_text("# Custom OpenCode preferences\n")
        installer.install(self.source, self.home)
        self.assertEqual(legacy.read_text(), "# Custom OpenCode preferences\n")
        legacy.unlink()
        custom = self.root / "custom-opencode.md"
        custom.write_text("# User-owned rules\n")
        legacy.symlink_to(custom)
        installer.install(self.source, self.home)
        self.assertEqual(legacy.resolve(), custom)
        self.assertEqual(custom.read_text(), "# User-owned rules\n")

    @unittest.skipUnless(os.access("/dev/shm", os.W_OK), "Needs another writable filesystem")
    def test_external_hermes_home_on_another_filesystem_installs_and_rolls_back(self):
        with tempfile.TemporaryDirectory(dir="/dev/shm") as directory:
            custom = Path(directory)
            if custom.stat().st_dev == self.home.stat().st_dev:
                self.skipTest("Temporary homes share the same filesystem")
            soul = custom / "SOUL.md"
            soul.write_text("# External personality\n")
            with patch.dict(os.environ, {"HERMES_HOME": str(custom)}):
                backup = installer.install(self.source, self.home)
                self.assertEqual(
                    (backup / "hermes-home/SOUL.md").read_text(),
                    "# External personality\n",
                )
                previous = soul.read_text()
                self.assertIn("# Shared rules\n", previous)
                (self.source / "AGENTS.md").write_text("# New rules\n")
                original = Path.rename

                def fail_after_hermes(path, target):
                    if path.name == "scoped-rules":
                        raise OSError("Simulated later replacement failure")
                    return original(path, target)

                with patch.object(Path, "rename", fail_after_hermes):
                    with self.assertRaisesRegex(OSError, "Simulated later"):
                        installer.install(self.source, self.home)
            self.assertEqual(soul.read_text(), previous)
            for entry in installer.ENTRIES:
                self.assertEqual((self.home / entry).read_text(), "# Shared rules\n")

    def test_failed_hermes_update_restores_personality_and_previous_rules(self):
        soul = self.home / ".hermes/SOUL.md"
        profile = self.home / ".hermes/profiles/work"
        profile.mkdir(parents=True)
        (profile / "config.yaml").write_text("{}\n")
        soul.write_text("# Personality\n")
        installer.install(self.source, self.home)
        previous_soul = soul.read_text()
        previous_profile = (profile / "SOUL.md").read_text()
        legacy = self.home / ".config/opencode/AGENTS.md"
        legacy.parent.mkdir(parents=True)
        legacy.symlink_to(self.home / ".agents/agent-rules/AGENTS.md")
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
        self.assertTrue(legacy.is_symlink())
        self.assertEqual(legacy.read_text(), "# Shared rules\n")
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
