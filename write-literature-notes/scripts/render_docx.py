#!/usr/bin/env python3
"""Render a DOCX to PDF with LibreOffice or Microsoft Word."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from xml.etree import ElementTree


HYPERLINK_RELATIONSHIP = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)
FORBIDDEN_OFFICE_PARTS = ("vbaproject.bin", "/activex/", "/embeddings/")
MAX_DOCX_MEMBERS = 10_000
MAX_DOCX_MEMBER_BYTES = 100 * 1024 * 1024
MAX_DOCX_TOTAL_BYTES = 500 * 1024 * 1024
MAX_DOCX_COMPRESSION_RATIO = 200
MAX_DOCX_XML_BYTES = 20 * 1024 * 1024
ALLOWED_HYPERLINK_SCHEMES = {"http", "https", "mailto"}


def assert_safe_docx_for_automation(path: Path) -> None:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            if len(members) > MAX_DOCX_MEMBERS:
                raise ValueError("input contains too many DOCX archive members")
            if len(names) != len(set(names)):
                raise ValueError("input contains duplicate DOCX archive members")
            if sum(member.file_size for member in members) > MAX_DOCX_TOTAL_BYTES:
                raise ValueError("input DOCX uncompressed size exceeds the safety limit")

            for member in members:
                member_path = PurePosixPath(member.filename.replace("\\", "/"))
                if (
                    member_path.is_absolute()
                    or ".." in member_path.parts
                    or (member_path.parts and member_path.parts[0].endswith(":"))
                ):
                    raise ValueError("input contains an unsafe DOCX archive path")
                if member.flag_bits & 0x1:
                    raise ValueError("input contains an encrypted DOCX archive member")
                if member.file_size > MAX_DOCX_MEMBER_BYTES or (
                    member.compress_size
                    and member.file_size / member.compress_size
                    > MAX_DOCX_COMPRESSION_RATIO
                ):
                    raise ValueError("input DOCX archive member exceeds a safety limit")
                if member.filename.lower().endswith((".xml", ".rels")):
                    if member.file_size > MAX_DOCX_XML_BYTES:
                        raise ValueError("input DOCX XML exceeds the safety limit")
                    xml = archive.read(member)
                    lowered_xml = xml.lower()
                    if b"<!doctype" in lowered_xml or b"<!entity" in lowered_xml:
                        raise ValueError("input DOCX XML contains a DTD or entity declaration")
                lowered = f"/{member.filename.lower()}"
                if (
                    any(part in lowered for part in FORBIDDEN_OFFICE_PARTS)
                    or "oleobject" in lowered
                ):
                    raise ValueError("input contains active or embedded Office content")
                if member.filename.lower().endswith(".rels"):
                    root = ElementTree.fromstring(xml)
                    for relationship in root:
                        if relationship.attrib.get("TargetMode", "").lower() != "external":
                            continue
                        if relationship.attrib.get("Type") != HYPERLINK_RELATIONSHIP:
                            raise ValueError(
                                "input contains a non-hyperlink external Office relationship"
                            )
                        target = relationship.attrib.get("Target", "")
                        if urlsplit(target).scheme.lower() not in ALLOWED_HYPERLINK_SCHEMES:
                            raise ValueError("input contains an unsafe Office hyperlink")
    except (zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError("input is not a valid DOCX archive") from exc


def assert_safe_output_path(path: Path) -> Path:
    output = path.absolute()
    for component in (output, *output.parents):
        is_junction = getattr(component, "is_junction", lambda: False)
        if component.is_symlink() or is_junction():
            raise ValueError("output path must not contain a symbolic link or junction")
    return output


def find_soffice() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    candidates = (
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path("/usr/bin/libreoffice"),
        Path("/usr/bin/soffice"),
    )
    return str(next((path for path in candidates if path.exists()), "")) or None


def render_with_soffice(source: Path, output: Path) -> bool:
    executable = find_soffice()
    if not executable:
        return False
    with tempfile.TemporaryDirectory(prefix="literature_note_render_") as temp_dir:
        temp_root = Path(temp_dir)
        profile = temp_root / "profile"
        out_dir = temp_root / "out"
        out_dir.mkdir()
        completed = subprocess.run(
            [
                executable,
                "--headless",
                f"-env:UserInstallation={profile.resolve().as_uri()}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        generated = out_dir / f"{source.stem}.pdf"
        if completed.returncode != 0 or not generated.is_file():
            return False
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(generated, output)
    return output.is_file()


def render_with_word(source: Path, output: Path) -> bool:
    if sys.platform != "win32" or not shutil.which("powershell.exe"):
        return False
    script = r'''
param([string]$SourcePath, [string]$OutputPath)
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $word.Options.UpdateLinksAtOpen = $false
    $document = $word.Documents.Open($SourcePath, $false, $true, $false)
    $document.ExportAsFixedFormat($OutputPath, 17)
    if (-not (Test-Path -LiteralPath $OutputPath)) { exit 1 }
}
catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
finally {
    if ($null -ne $document) { $document.Close($false) }
    if ($null -ne $word) { $word.Quit() }
}
'''
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ps1", encoding="utf-8-sig", delete=False
    ) as handle:
        handle.write(script)
        script_path = Path(handle.name)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(script_path),
                "-SourcePath",
                str(source),
                "-OutputPath",
                str(output),
            ],
            capture_output=True,
            text=True,
        )
        return completed.returncode == 0 and output.is_file()
    finally:
        script_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument(
        "--renderer", choices=("auto", "libreoffice", "word"), default="auto"
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.input.resolve()
    output = assert_safe_output_path(args.pdf)
    if source.suffix.lower() != ".docx" or not source.is_file():
        raise ValueError("input must be an existing .docx file")
    assert_safe_docx_for_automation(source)
    if output.suffix.lower() != ".pdf":
        raise ValueError("--pdf must end with .pdf")
    if output.exists() and not args.force:
        raise FileExistsError(f"output already exists: {output}; pass --force to replace it")

    renderer = None
    if args.renderer in ("auto", "libreoffice") and render_with_soffice(source, output):
        renderer = "libreoffice"
    elif args.renderer in ("auto", "word") and render_with_word(source, output):
        renderer = "microsoft-word"
    if renderer is None:
        raise RuntimeError(
            "no usable renderer; install LibreOffice or Microsoft Word, then retry"
        )

    print(
        json.dumps(
            {"status": "pass", "renderer": renderer, "pdf": str(output)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2),
            file=sys.stderr,
        )
        raise SystemExit(2)
