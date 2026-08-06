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
from pathlib import Path


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
    output = args.pdf.resolve()
    if source.suffix.lower() != ".docx" or not source.is_file():
        raise ValueError("input must be an existing .docx file")
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
