#!/usr/bin/env python3
"""Check whether this skill can build and render its locked DOCX template."""

from __future__ import annotations

import hashlib
import importlib.util
from importlib import metadata
import json
import re
import shutil
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows
    winreg = None


ASSET_HASHES = {
    "reading-note-template.docx": "B2E31C1B2CF8870810F596E725F48088DB2DDFBC7E629CC60262BB8A75A5F932",
    "teacher-reference.docx": "FAED7BA4511380925BE4AD27E4EFDAF6AE3DC235AB20EB4984586C4CB91371AB",
    "recent-style-reference.docx": "B4A39E8393BF5FE81EBBAC1B80DCDC934F957688613E4E25750A94BFFBB67AF3",
}
REQUIRED_PACKAGES = {
    "python-docx": ("docx", (1, 2, 0), 2),
    "lxml": ("lxml", (5, 0, 0), 7),
}


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(number) for number in re.findall(r"\d+", value)[:3])


def version_supported(value: str | None, minimum: tuple[int, ...], maximum_major: int) -> bool:
    if value is None:
        return False
    parsed = version_tuple(value)
    return bool(parsed) and parsed >= minimum and parsed[0] < maximum_major


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
        for name, (module, _, _) in REQUIRED_PACKAGES.items()
    }
    versions = {
        name: metadata.version(name) if packages[name] else None
        for name in REQUIRED_PACKAGES
    }
    versions_match = {
        name: version_supported(versions[name], minimum, maximum_major)
        for name, (_, minimum, maximum_major) in REQUIRED_PACKAGES.items()
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
        and all(versions_match.values())
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
        actions.append(
            "Select another Python environment or, after approval, create an isolated "
            "environment and install scripts/requirements.txt. Missing: "
            + ", ".join(missing)
        )
    mismatched = [
        f"{name}={versions[name]} (supported >= {minimum} and < {maximum_major}.0.0)"
        for name, (_, minimum, maximum_major) in REQUIRED_PACKAGES.items()
        if packages[name] and not versions_match[name]
    ]
    if mismatched:
        actions.append(
            "Use compatible versions from scripts/requirements.txt in an isolated "
            "environment. Version mismatch: "
            + ", ".join(mismatched)
        )
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
        "versions": versions,
        "versions_match": versions_match,
        "assets": assets,
        "renderers": {"libreoffice": soffice, "microsoft_word": word},
        "actions": actions,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
