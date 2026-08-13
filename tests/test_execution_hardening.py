from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class ExecutionHardeningTests(unittest.TestCase):
    def test_repository_preflight_disables_git_fsmonitor(self) -> None:
        module = load_script(
            "project_check_environment",
            ROOT / "project-learning-sop" / "scripts" / "check_environment.py",
        )
        with patch.object(module.subprocess, "run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "ok\n"
            module.run_git("git", ROOT, "status", "--short")
        command = run.call_args.args[0]
        self.assertIn("core.fsmonitor=false", command)
        self.assertLess(command.index("core.fsmonitor=false"), command.index("-C"))

    def test_word_automation_forces_macros_and_link_updates_off(self) -> None:
        paths = (
            ROOT / "word-writer" / "scripts" / "normalize_word.py",
            ROOT / "word-writer" / "scripts" / "render_docx.py",
            ROOT / "write-literature-notes" / "scripts" / "render_docx.py",
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("AutomationSecurity", text)
                self.assertIn("UpdateLinksAtOpen", text)

    def test_docx_automation_entry_points_reject_local_file_hyperlinks(self) -> None:
        relationship_type = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
        )
        paths = (
            ROOT / "word-writer" / "scripts" / "normalize_word.py",
            ROOT / "word-writer" / "scripts" / "render_docx.py",
            ROOT / "write-literature-notes" / "scripts" / "render_docx.py",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir) / "unsafe.docx"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("[Content_Types].xml", "<Types/>")
                output.writestr("word/document.xml", "<document/>")
                output.writestr(
                    "word/_rels/document.xml.rels",
                    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    f'<Relationship Id="rId1" Type="{relationship_type}" '
                    'Target="file:///private/reference" TargetMode="External"/>'
                    "</Relationships>",
                )
            for index, path in enumerate(paths):
                with self.subTest(path=path):
                    module = load_script(f"docx_entry_{index}", path)
                    with self.assertRaisesRegex(ValueError, "unsafe Office hyperlink"):
                        module.assert_safe_docx_for_automation(archive)

    def test_output_safety_rejects_a_linked_parent_directory(self) -> None:
        paths = (
            ROOT / "word-writer" / "scripts" / "normalize_word.py",
            ROOT / "word-writer" / "scripts" / "render_docx.py",
            ROOT / "write-literature-notes" / "scripts" / "fill_reading_note.py",
            ROOT / "write-literature-notes" / "scripts" / "render_docx.py",
        )
        output = Path("safe-root") / "linked-parent" / "output.docx"
        original = Path.is_symlink
        for index, path in enumerate(paths):
            with self.subTest(path=path):
                module = load_script(f"output_entry_{index}", path)
                with patch.object(
                    Path,
                    "is_symlink",
                    autospec=True,
                    side_effect=lambda item: item.name == "linked-parent"
                    or original(item),
                ):
                    with self.assertRaisesRegex(ValueError, "symbolic link or junction"):
                        module.assert_safe_output_path(output)


if __name__ == "__main__":
    unittest.main()
