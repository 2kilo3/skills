#!/usr/bin/env python3
"""Scan a skill folder for credentials, private paths, and risky secret files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "node_modules",
}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".rels",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
ARCHIVE_SUFFIXES = {".docx", ".pptx", ".xlsx", ".zip"}
MAX_TEXT_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_TEXT_BYTES = 20 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000

PATTERNS = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
        "private key material",
    ),
    (
        "aws-access-key",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "AWS access key identifier",
    ),
    (
        "openai-key",
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
        "OpenAI-style API key",
    ),
    (
        "github-token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
        "GitHub token",
    ),
    (
        "slack-token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
        "Slack token",
    ),
    (
        "google-api-key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
        "Google API key",
    ),
    (
        "stripe-live-key",
        re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b"),
        "Stripe live key",
    ),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        "JSON Web Token",
    ),
    (
        "authorization-header",
        re.compile(
            r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+[A-Za-z0-9._~+/-]{12,}=*"
        ),
        "embedded Authorization header",
    ),
    (
        "credential-url",
        re.compile(r"(?i)\b(?:https?|ssh)://[^\s/@:]+:[^\s/@]+@[^\s]+"),
        "URL containing embedded credentials",
    ),
    (
        "secret-assignment",
        re.compile(
            r"""(?ix)
            \b(?:api[_-]?key|access[_-]?key|client[_-]?secret|password|passwd|secret|token)\b
            \s*[:=]\s*["']?
            ([A-Za-z0-9_./+=:-]{8,})
            """
        ),
        "hard-coded secret-like assignment",
    ),
    (
        "personal-path",
        re.compile(
            r"""(?ix)
            (?:[A-Z]:\\Users\\(?!Public\\|Default\\|<)[^\\\r\n]+\\)
            |
            (?:/(?:Users|home)/(?!<)[^/\s]+/)
            """
        ),
        "machine-specific user directory",
    ),
)

PLACEHOLDER_VALUES = {
    "changeme",
    "example",
    "placeholder",
    "redacted",
    "replace-me",
    "replace_me",
    "your-key",
    "your_key",
}
SUSPICIOUS_FILENAMES = {
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
    "service-account.json",
}


def relative_label(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def suspicious_name(path: Path) -> str | None:
    name = path.name.lower()
    if name == ".env" or (
        name.startswith(".env.")
        and name not in {".env.example", ".env.sample", ".env.template"}
    ):
        return "environment file may contain live credentials"
    if name in SUSPICIOUS_FILENAMES:
        return "credential-bearing filename"
    if re.fullmatch(r"(?:secret|secrets|credentials?)(?:\.[^.]+)?", name):
        return "secret-bearing filename"
    return None


def is_placeholder(match: re.Match[str]) -> bool:
    if match.lastindex is None:
        return False
    value = match.group(1).lower()
    return (
        value in PLACEHOLDER_VALUES
        or value.startswith(("example-", "fake-", "test-", "your-"))
        or value.endswith(("-example", "-placeholder"))
        or "..." in value
        or "xxx" in value
    )


def scan_text(text: str, label: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for rule, pattern, reason in PATTERNS:
        for match in pattern.finditer(text):
            if rule == "secret-assignment" and is_placeholder(match):
                continue
            findings.append(
                {
                    "severity": "error",
                    "rule": rule,
                    "path": label,
                    "line": text.count("\n", 0, match.start()) + 1,
                    "reason": reason,
                }
            )
    return findings


def iter_files(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = [name for name in directories if name not in EXCLUDED_DIRS]
        base = Path(current)
        for name in files:
            yield base / name


def archive_member_is_text(name: str) -> bool:
    path = Path(name)
    return path.suffix.lower() in TEXT_SUFFIXES or path.name == "[Content_Types].xml"


def scan_archive(
    path: Path, root: Path
) -> tuple[list[dict[str, object]], list[dict[str, str]], int]:
    findings: list[dict[str, object]] = []
    warnings: list[dict[str, str]] = []
    scanned = 0
    consumed = 0
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                warnings.append(
                    {
                        "path": relative_label(path, root),
                        "reason": "archive member limit exceeded; manual review required",
                    }
                )
                return findings, warnings, scanned
            for member in members:
                if member.is_dir() or not archive_member_is_text(member.filename):
                    continue
                if member.file_size > MAX_TEXT_BYTES:
                    warnings.append(
                        {
                            "path": f"{relative_label(path, root)}!{member.filename}",
                            "reason": "archive text member exceeds scan size limit",
                        }
                    )
                    continue
                consumed += member.file_size
                if consumed > MAX_ARCHIVE_TEXT_BYTES:
                    warnings.append(
                        {
                            "path": relative_label(path, root),
                            "reason": "archive text budget exceeded; manual review required",
                        }
                    )
                    break
                text = archive.read(member).decode("utf-8", errors="replace")
                findings.extend(
                    scan_text(text, f"{relative_label(path, root)}!{member.filename}")
                )
                scanned += 1
    except (OSError, zipfile.BadZipFile) as exc:
        warnings.append(
            {
                "path": relative_label(path, root),
                "reason": f"archive could not be inspected: {type(exc).__name__}",
            }
        )
    return findings, warnings, scanned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="skill directory; defaults to the parent of this script directory",
    )
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(
            json.dumps(
                {"status": "error", "error": f"skill directory does not exist: {root}"},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2

    findings: list[dict[str, object]] = []
    warnings: list[dict[str, str]] = []
    text_files_scanned = 0
    archive_members_scanned = 0

    for path in iter_files(root):
        if path.is_symlink():
            findings.append(
                {
                    "severity": "error",
                    "rule": "symlink",
                    "path": relative_label(path, root),
                    "line": None,
                    "reason": "skill file symlink may expose content outside the skill",
                }
            )
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue

        filename_reason = suspicious_name(path)
        if filename_reason:
            findings.append(
                {
                    "severity": "error",
                    "rule": "suspicious-filename",
                    "path": relative_label(path, root),
                    "line": None,
                    "reason": filename_reason,
                }
            )

        suffix = path.suffix.lower()
        if suffix in ARCHIVE_SUFFIXES:
            archive_findings, archive_warnings, scanned = scan_archive(path, root)
            findings.extend(archive_findings)
            warnings.extend(archive_warnings)
            archive_members_scanned += scanned
            continue

        if suffix not in TEXT_SUFFIXES:
            warnings.append(
                {
                    "path": relative_label(path, root),
                    "reason": "binary or unsupported file requires manual provenance review",
                }
            )
            continue
        try:
            if path.stat().st_size > MAX_TEXT_BYTES:
                warnings.append(
                    {
                        "path": relative_label(path, root),
                        "reason": "text file exceeds scan size limit",
                    }
                )
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            warnings.append(
                {
                    "path": relative_label(path, root),
                    "reason": f"file could not be read: {type(exc).__name__}",
                }
            )
            continue
        findings.extend(scan_text(text, relative_label(path, root)))
        text_files_scanned += 1

    report = {
        "status": "pass" if not findings and not warnings else "fail",
        "root": str(root),
        "text_files_scanned": text_files_scanned,
        "archive_members_scanned": archive_members_scanned,
        "findings": findings,
        "warnings": warnings,
        "redaction": "matched values are intentionally omitted",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

