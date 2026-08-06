#!/usr/bin/env python3
"""Report Word Writer capabilities without importing optional packages."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows
    winreg = None


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


def detect_fonts() -> dict[str, bool | None]:
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        font_dir = windir / "Fonts"
        return {
            "SimHei": any((font_dir / name).is_file() for name in ("simhei.ttf",)),
            "Microsoft YaHei": any(
                (font_dir / name).is_file()
                for name in ("msyh.ttc", "msyh.ttf", "msyhbd.ttc")
            ),
        }

    fc_list = shutil.which("fc-list")
    if fc_list:
        completed = subprocess.run(
            [fc_list, ":", "family"], capture_output=True, text=True
        )
        families = completed.stdout.lower()
        return {
            "SimHei": "simhei" in families or "黑体" in families,
            "Microsoft YaHei": "microsoft yahei" in families or "微软雅黑" in families,
        }
    return {"SimHei": None, "Microsoft YaHei": None}


def main() -> int:
    packages = {
        name: importlib.util.find_spec(module) is not None
        for name, module in {"python-docx": "docx", "lxml": "lxml"}.items()
    }
    fonts = detect_fonts()
    soffice = find_soffice()
    word = has_word_com()
    core_ready = sys.version_info >= (3, 10) and all(packages.values())
    render_ready = bool(soffice or word)
    fonts_ready = all(value is True for value in fonts.values())
    status = "ready" if core_ready and render_ready and fonts_ready else "degraded"
    if not core_ready:
        status = "blocked"

    actions = []
    if sys.version_info < (3, 10):
        actions.append("Use Python 3.10 or newer.")
    missing = [name for name, available in packages.items() if not available]
    if missing:
        actions.append("Select a Python environment containing: " + ", ".join(missing))
    if not fonts_ready:
        actions.append("Install SimHei and Microsoft YaHei, or obtain approval for substitutes.")
    if not render_ready:
        actions.append("Install LibreOffice or Microsoft Word for conversion and visual QA.")

    report = {
        "status": status,
        "core": {"status": "ready" if core_ready else "blocked", "packages": packages},
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "utf8_mode": bool(sys.flags.utf8_mode),
        },
        "fonts": fonts,
        "renderers": {"libreoffice": soffice, "microsoft_word": word},
        "actions": actions,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
