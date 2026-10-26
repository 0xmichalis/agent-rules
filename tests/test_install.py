import importlib.util
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


if __name__ == "__main__":
    unittest.main()
