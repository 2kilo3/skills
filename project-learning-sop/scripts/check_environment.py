#!/usr/bin/env python3
"""Report host and repository capabilities for Project Learning SOP."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
FILE_COUNT_LIMIT = 50_000


def run_git(git: str, repo: Path, *arguments: str) -> str | None:
    completed = subprocess.run(
        [git, "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def inventory_repository(repo: Path, git: str | None) -> dict[str, object]:
    file_count = 0
    total_bytes = 0
    truncated = False
    markers: list[str] = []
    marker_names = {
        "Cargo.toml",
        "Dockerfile",
        "Makefile",
        "Taskfile.yml",
        "go.mod",
        "package.json",
        "pom.xml",
        "pyproject.toml",
        "requirements.txt",
    }

    for current, directories, files in os.walk(repo):
        directories[:] = [name for name in directories if name not in EXCLUDED_DIRS]
        relative_root = Path(current).relative_to(repo)
        for name in files:
            file_count += 1
            path = Path(current) / name
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass
            if len(relative_root.parts) <= 1 and name in marker_names:
                markers.append((relative_root / name).as_posix())
            if file_count >= FILE_COUNT_LIMIT:
                truncated = True
                break
        if truncated:
            break

    if truncated or file_count > 20_000:
        resource_mode = "staged"
    elif file_count > 2_000:
        resource_mode = "targeted"
    else:
        resource_mode = "full"

    git_info: dict[str, object] = {
        "available": bool(git),
        "is_repository": False,
        "commit": None,
        "shallow": None,
        "dirty_entries": None,
    }
    if git:
        root = run_git(git, repo, "rev-parse", "--show-toplevel")
        if root:
            status = run_git(git, repo, "status", "--short")
            git_info.update(
                {
                    "is_repository": True,
                    "commit": run_git(git, repo, "rev-parse", "HEAD"),
                    "shallow": run_git(
                        git, repo, "rev-parse", "--is-shallow-repository"
                    )
                    == "true",
                    "dirty_entries": len(status.splitlines()) if status else 0,
                }
            )

    return {
        "path": str(repo),
        "file_count": file_count,
        "file_count_truncated": truncated,
        "approximate_bytes": total_bytes,
        "top_level_markers": sorted(markers),
        "resource_mode": resource_mode,
        "git": git_info,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="optional local repository path")
    args = parser.parse_args()

    git = shutil.which("git")
    ripgrep = shutil.which("rg")
    python_ready = sys.version_info >= (3, 10)
    status = "ready" if python_ready and git and ripgrep else "degraded"
    actions: list[str] = []

    if not python_ready:
        status = "blocked"
        actions.append("Use Python 3.10 or newer for the bundled validators.")
    if not git:
        actions.append(
            "Install Git before cloning GitHub repositories or using history evidence."
        )
    if not ripgrep:
        actions.append(
            "Install ripgrep for fast targeted search, or use the platform search fallback."
        )

    repository = None
    if args.repo is not None:
        repo = args.repo.expanduser().resolve()
        if not repo.is_dir():
            status = "blocked"
            actions.append(f"Provide an existing repository directory: {repo}")
        else:
            repository = inventory_repository(repo, git)
            if repository["resource_mode"] == "staged":
                actions.append(
                    "Use staged discovery: map manifests and entry points first, then scan only the selected subsystem."
                )

    report = {
        "status": status,
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "utf8_mode": bool(sys.flags.utf8_mode),
        },
        "commands": {"git": git, "rg": ripgrep},
        "repository": repository,
        "actions": actions,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
