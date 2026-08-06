#!/usr/bin/env python3
"""Check whether this skill can build and render its locked DOCX template."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows
    winreg = None


ASSET_HASHES = {
    "reading-note-template.docx": "4824159895BDA6297DEF7DEFDCE79CD406D88BE40C6D9ED4AA9ABBEF680A387C",
    "teacher-reference.docx": "55193C302629F43710772B41191EB83FDCEE2DE0F8A22C13D217297D8939A5BE",
    "recent-style-reference.docx": "8B299A53899E773E48DC92170E603659FE5E4EE2EC6FB30137B166A151FCEB5F",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


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


def has_word_com() -> bool:
    if sys.platform != "win32" or winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"):
            return True
    except OSError:
        return False


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    assets_dir = skill_dir / "assets"
    packages = {
        name: importlib.util.find_spec(module) is not None
        for name, module in {"python-docx": "docx", "lxml": "lxml"}.items()
    }
    assets = {}
    for name, expected in ASSET_HASHES.items():
        path = assets_dir / name
        actual = sha256(path) if path.is_file() else None
        assets[name] = {
            "present": path.is_file(),
            "sha256_ok": actual == expected,
            "actual_sha256": actual,
        }

    soffice = find_soffice()
    word = has_word_com()
    core_ready = (
        sys.version_info >= (3, 10)
        and all(packages.values())
        and assets["reading-note-template.docx"]["sha256_ok"]
    )
    renderer_ready = bool(soffice or word)
    status = "ready" if core_ready and renderer_ready else "degraded"
    if not core_ready:
        status = "blocked"

    actions = []
    if sys.version_info < (3, 10):
        actions.append("Use Python 3.10 or newer.")
    missing = [name for name, available in packages.items() if not available]
    if missing:
        actions.append("Select a Python environment containing: " + ", ".join(missing))
    if not assets["reading-note-template.docx"]["sha256_ok"]:
        actions.append("Restore the locked reading-note-template.docx asset.")
    if not renderer_ready:
        actions.append(
            "Install LibreOffice or Microsoft Word, or use another installed DOCX renderer; "
            "structural generation can proceed only when status is not blocked."
        )

    report = {
        "status": status,
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "utf8_mode": bool(sys.flags.utf8_mode),
        },
        "packages": packages,
        "assets": assets,
        "renderers": {"libreoffice": soffice, "microsoft_word": word},
        "actions": actions,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
