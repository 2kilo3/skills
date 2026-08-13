from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPTS = (
    ROOT / "project-learning-sop" / "scripts" / "audit_skill_security.py",
    ROOT / "word-writer" / "scripts" / "audit_skill_security.py",
    ROOT / "write-literature-notes" / "scripts" / "audit_skill_security.py",
)


def load_audit(path: Path, index: int):
    specification = importlib.util.spec_from_file_location(f"security_audit_{index}", path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def write_docx(path: Path, members: dict[str, str | bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


class SecurityAuditTests(unittest.TestCase):
    def test_archive_scanner_rejects_external_and_active_content(self) -> None:
        malicious_members = {
            "[Content_Types].xml": "<Types/>",
            "word/document.xml": "<document/>",
            "word/_rels/document.xml.rels": (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://example.invalid/image" '
                'Target="https://example.invalid/tracker" TargetMode="External"/>'
                "</Relationships>"
            ),
            "word/vbaProject.bin": b"not-a-real-macro",
            "word/embeddings/object1.bin": b"not-a-real-object",
        }
        for index, script in enumerate(AUDIT_SCRIPTS):
            with self.subTest(script=script):
                audit = load_audit(script, index)
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    archive = root / "malicious.docx"
                    write_docx(archive, malicious_members)
                    findings, warnings, _scanned = audit.scan_archive(archive, root)
                rules = {finding["rule"] for finding in findings}
                self.assertIn("external-relationship", rules)
                self.assertIn("active-content", rules)
                self.assertIn("embedded-object", rules)
                self.assertEqual(warnings, [])

    def test_archive_scanner_allows_an_external_hyperlink(self) -> None:
        relationship_type = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
        )
        members = {
            "[Content_Types].xml": "<Types/>",
            "word/document.xml": "<document/>",
            "word/_rels/document.xml.rels": (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rId1" Type="{relationship_type}" '
                'Target="https://example.invalid/reference" TargetMode="External"/>'
                "</Relationships>"
            ),
        }
        audit = load_audit(AUDIT_SCRIPTS[-1], 101)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "hyperlink.docx"
            write_docx(archive, members)
            findings, warnings, _scanned = audit.scan_archive(archive, root)
        self.assertEqual(findings, [])
        self.assertEqual(warnings, [])

    def test_archive_scanner_rejects_local_file_hyperlink_and_dtd(self) -> None:
        relationship_type = (
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
        )
        members = {
            "[Content_Types].xml": "<Types/>",
            "word/document.xml": '<!DOCTYPE document [<!ENTITY x "unsafe">]><document/>',
            "word/_rels/document.xml.rels": (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rId1" Type="{relationship_type}" '
                'Target="file:///private/reference" TargetMode="External"/>'
                "</Relationships>"
            ),
        }
        audit = load_audit(AUDIT_SCRIPTS[-1], 102)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "unsafe.docx"
            write_docx(archive, members)
            findings, warnings, _scanned = audit.scan_archive(archive, root)
        rules = {finding["rule"] for finding in findings}
        self.assertIn("external-relationship", rules)
        self.assertIn("unsafe-xml-declaration", rules)
        self.assertEqual(warnings, [])

    def test_archive_scanner_rejects_backslash_traversal(self) -> None:
        audit = load_audit(AUDIT_SCRIPTS[-1], 103)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "unsafe-path.docx"
            write_docx(archive, {"word\\..\\private.xml": "<private/>"})
            findings, warnings, _scanned = audit.scan_archive(archive, root)
        self.assertIn(
            "unsafe-archive-path", {finding["rule"] for finding in findings}
        )
        self.assertEqual(warnings, [])

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks are unavailable")
    def test_iter_files_reports_symlinked_files_and_directories(self) -> None:
        for index, script in enumerate(AUDIT_SCRIPTS):
            with self.subTest(script=script):
                audit = load_audit(script, index)
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    outside = root / "outside"
                    outside.mkdir()
                    (outside / "secret.txt").write_text("outside", encoding="utf-8")
                    file_link = root / "file-link"
                    directory_link = root / "directory-link"
                    try:
                        file_link.symlink_to(outside / "secret.txt")
                        directory_link.symlink_to(outside, target_is_directory=True)
                    except OSError as exc:
                        self.skipTest(f"symlink creation is unavailable: {exc}")
                    paths = {path.name: path for path in audit.iter_files(root)}
                self.assertTrue(paths["file-link"].is_symlink())
                self.assertTrue(paths["directory-link"].is_symlink())

    def test_iter_files_yields_directory_symlinks_without_traversing_them(self) -> None:
        for index, script in enumerate(AUDIT_SCRIPTS):
            with self.subTest(script=script):
                audit = load_audit(script, index)
                root = Path("audit-root").absolute()
                walk_result = [(str(root), ["directory-link", "real"], ["file-link"])]
                with patch.object(audit.os, "walk", return_value=walk_result), patch.object(
                    audit.Path,
                    "is_symlink",
                    autospec=True,
                    side_effect=lambda path: path.name in {"directory-link", "file-link"},
                ):
                    paths = list(audit.iter_files(root))
                self.assertEqual(
                    [path.name for path in paths], ["directory-link", "file-link"]
                )
                self.assertEqual(walk_result[0][1], ["real"])

    def test_bundled_office_assets_remain_acceptable(self) -> None:
        audit = load_audit(AUDIT_SCRIPTS[-1], 99)
        skill_root = ROOT / "write-literature-notes"
        for archive in sorted((skill_root / "assets").glob("*.docx")):
            with self.subTest(archive=archive.name):
                findings, warnings, scanned = audit.scan_archive(archive, skill_root)
                self.assertEqual(findings, [])
                self.assertEqual(warnings, [])
                self.assertGreater(scanned, 0)

    def test_encrypted_archive_member_is_reported_without_reading(self) -> None:
        audit = load_audit(AUDIT_SCRIPTS[-1], 100)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "encrypted.docx"
            with zipfile.ZipFile(archive, "w") as output:
                info = zipfile.ZipInfo("word/document.xml")
                info.flag_bits |= 0x1
                output.writestr(info, "<document/>")
            with zipfile.ZipFile(archive, "r") as stored:
                stored.getinfo("word/document.xml").flag_bits |= 0x1
                with patch.object(stored, "read", side_effect=RuntimeError("encrypted")):
                    with patch.object(audit.zipfile, "ZipFile", return_value=stored):
                        findings, warnings, scanned = audit.scan_archive(archive, root)
        self.assertEqual(findings, [])
        self.assertEqual(scanned, 0)
        self.assertTrue(any("encrypted" in warning["reason"] for warning in warnings))


if __name__ == "__main__":
    unittest.main()
