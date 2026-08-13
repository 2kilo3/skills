from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docx import Document


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


class OutputSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.word_writer = load_script(
            "normalize_word",
            ROOT / "word-writer" / "scripts" / "normalize_word.py",
        )
        cls.literature_notes = load_script(
            "fill_reading_note",
            ROOT / "write-literature-notes" / "scripts" / "fill_reading_note.py",
        )

    def test_word_writer_does_not_overwrite_predictable_sibling_temp_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "output.docx"
            Document().save(document_path)
            predictable = root / ".output.docx.formatting.tmp"
            predictable.write_text("owned-by-user", encoding="utf-8")

            self.word_writer.normalize_all_wordprocessing_runs(
                document_path, self.word_writer.StyleProfile()
            )

            self.assertEqual(predictable.read_text(encoding="utf-8"), "owned-by-user")

    def test_literature_note_builder_rejects_symlink_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "output.docx"
            original = Path.is_symlink
            with patch.object(
                Path,
                "is_symlink",
                autospec=True,
                side_effect=lambda path: path == output or original(path),
            ):
                with self.assertRaisesRegex(ValueError, "symbolic link"):
                    self.literature_notes.build(
                        ROOT
                        / "write-literature-notes"
                        / "assets"
                        / "reading-note-template.docx",
                        root / "unused.json",
                        output,
                        force=True,
                    )


if __name__ == "__main__":
    unittest.main()
