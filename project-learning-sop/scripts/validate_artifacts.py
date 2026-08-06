#!/usr/bin/env python3
"""Validate Project Learning SOP guide and course artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


LINE_RANGE = re.compile(r"^(\d+)(?:\s*-\s*(\d+))?$")
BASELINE = re.compile(r"^>\s*源码基线：\s*(.+)$", re.MULTILINE)


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def resolve_repo_file(repo: Path, relative: str) -> tuple[Path | None, str | None]:
    relative = clean_cell(relative).replace("\\", "/")
    if not relative or "<br" in relative.lower() or "→" in relative:
        return None, "每个导航行必须只包含一个仓库相对路径"
    candidate = Path(relative)
    if candidate.is_absolute():
        return None, "源码路径必须是仓库相对路径"
    resolved = (repo / candidate).resolve()
    try:
        resolved.relative_to(repo)
    except ValueError:
        return None, "源码路径越出仓库根目录"
    if not resolved.is_file():
        return None, f"文件不存在：{relative}"
    return resolved, None


def symbol_candidates(value: str) -> list[str]:
    value = clean_cell(value)
    value = re.sub(r"\(.*\)$", "", value).strip()
    candidates = [value]
    if "." in value:
        candidates.append(value.rsplit(".", 1)[-1])
    return [item for item in dict.fromkeys(candidates) if item]


def parse_markdown_table(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        if cells[0] in {"我想理解/修改什么", "核心功能"}:
            continue
        rows.append(cells)
    return rows


def validate_guide(guide: Path, repo: Path, min_rows: int) -> list[str]:
    errors: list[str] = []
    text = guide.read_text(encoding="utf-8")

    if not BASELINE.search(text):
        errors.append("缺少“> 源码基线：...”")
    for number in range(1, 11):
        if not re.search(rf"^##\s+{number}\.", text, re.MULTILINE):
            errors.append(f"缺少第 {number} 节")
    if re.search(r"!\[[^\]]*\]\([^)]+\)", text):
        errors.append("guide.md 不得引用外部图片资产；使用 mermaid + ASCII")

    match = re.search(
        r"^##\s+5\.\s+功能\s*→\s*文件\s*→\s*代码导航表.*?(?=^##\s+6\.)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        errors.append("未找到第 5 节功能→文件→代码导航表")
        return errors

    rows = parse_markdown_table(match.group(0))
    if len(rows) < min_rows:
        errors.append(f"导航表有效行数 {len(rows)}，少于要求的 {min_rows}")

    for index, row in enumerate(rows, start=1):
        label = f"导航表第 {index} 行"
        if len(row) != 5:
            errors.append(f"{label}应有 5 列，实际 {len(row)} 列")
            continue
        source, source_error = resolve_repo_file(repo, row[1])
        if source_error:
            errors.append(f"{label}：{source_error}")
            continue

        line_value = clean_cell(row[3])
        line_match = LINE_RANGE.fullmatch(line_value)
        if not line_match:
            errors.append(f"{label}行号必须是精确整数或区间：{line_value}")
            continue
        start = int(line_match.group(1))
        end = int(line_match.group(2) or start)
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        if start < 1 or end < start or end > len(lines):
            errors.append(f"{label}行号越界：{start}-{end}，文件共 {len(lines)} 行")
            continue

        candidates = symbol_candidates(row[2])
        excerpt = "\n".join(lines[start - 1 : end])
        if not candidates or not any(candidate in excerpt for candidate in candidates):
            errors.append(f"{label}的符号未出现在指定行范围：{clean_cell(row[2])}")

    return errors


class CourseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.nav_targets: list[str] = []
        self.modules: dict[str, dict[str, int]] = {}
        self.current_module: str | None = None
        self.module_depth = 0
        self.has_style = False
        self.has_script = False
        self.has_flow = False
        self.has_chat = False
        self.has_term = False
        self.external_resources: list[str] = []
        self.invalid_images: list[str] = []
        self.source_blocks: list[dict[str, str]] = []
        self.current_source: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = set(values.get("class", "").split())
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)

        for attribute in ("src", "href"):
            value = values.get(attribute, "").strip()
            if value.startswith(("http://", "https://", "//")):
                self.external_resources.append(value)
        if tag == "img" and not values.get("src", "").startswith("data:"):
            self.invalid_images.append(values.get("src", "<missing>"))

        if tag == "style":
            self.has_style = True
        if tag == "script":
            self.has_script = True
        if tag == "button" and values.get("data-target"):
            self.nav_targets.append(values["data-target"])

        if tag == "section" and "module" in classes:
            module_id = element_id or f"<module-{len(self.modules) + 1}>"
            self.current_module = module_id
            self.module_depth = 1
            self.modules[module_id] = {
                "quiz": 0,
                "source": 0,
                "code_pair": 0,
                "plain_side": 0,
            }
        elif tag == "section" and self.current_module:
            self.module_depth += 1

        if tag == "details" and "quiz" in classes and self.current_module:
            self.modules[self.current_module]["quiz"] += 1
        if "code-pair" in classes and self.current_module:
            self.modules[self.current_module]["code_pair"] += 1
        if "plain-side" in classes and self.current_module:
            self.modules[self.current_module]["plain_side"] += 1
        if tag == "ol" and "flow" in classes:
            self.has_flow = True
        if "chat" in classes:
            self.has_chat = True
        if "term" in classes:
            self.has_term = True

        if tag == "pre" and values.get("data-source"):
            self.current_source = {
                "path": values["data-source"],
                "lines": values.get("data-lines", ""),
                "text": "",
                "module": self.current_module or "",
            }
            if self.current_module:
                self.modules[self.current_module]["source"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self.current_source is not None:
            self.source_blocks.append(self.current_source)
            self.current_source = None
        if tag == "section" and self.current_module:
            self.module_depth -= 1
            if self.module_depth == 0:
                self.current_module = None

    def handle_data(self, data: str) -> None:
        if self.current_source is not None:
            self.current_source["text"] += data


def validate_source_block(block: dict[str, str], repo: Path) -> list[str]:
    errors: list[str] = []
    source, source_error = resolve_repo_file(repo, block["path"])
    label = f"代码块 {block['path']}:{block['lines'] or '?'}"
    if source_error:
        return [f"{label}：{source_error}"]
    line_match = LINE_RANGE.fullmatch(block["lines"].strip())
    if not line_match:
        return [f"{label}缺少有效 data-lines"]
    start = int(line_match.group(1))
    end = int(line_match.group(2) or start)
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    if start < 1 or end < start or end > len(lines):
        return [f"{label}行号越界，文件共 {len(lines)} 行"]
    expected = "\n".join(lines[start - 1 : end]).strip("\r\n")
    actual = block["text"].strip("\r\n")
    if actual != expected:
        errors.append(f"{label}未与源码逐字匹配")
    return errors


def validate_course(course: Path, repo: Path, min_modules: int, max_modules: int) -> list[str]:
    errors: list[str] = []
    text = course.read_text(encoding="utf-8")
    parser = CourseParser()
    parser.feed(text)

    module_count = len(parser.modules)
    if not min_modules <= module_count <= max_modules:
        errors.append(f"课程模块数 {module_count}，要求 {min_modules}-{max_modules}")
    if not parser.has_style or not parser.has_script:
        errors.append("course.html 必须内嵌 style 与 script")
    if parser.external_resources:
        errors.append("存在外部资源：" + ", ".join(parser.external_resources))
    if parser.invalid_images:
        errors.append("图片必须使用 data URI：" + ", ".join(parser.invalid_images))
    missing_targets = [target for target in parser.nav_targets if target not in parser.ids]
    non_module_targets = [
        target for target in parser.nav_targets if target not in parser.modules
    ]
    missing_module_buttons = [
        module_id for module_id in parser.modules if module_id not in parser.nav_targets
    ]
    duplicate_targets = sorted(
        {
            target
            for target in parser.nav_targets
            if parser.nav_targets.count(target) > 1
        }
    )
    if not parser.nav_targets:
        errors.append("导航栏缺少 data-target 按钮")
    elif missing_targets:
        errors.append("导航目标不存在：" + ", ".join(missing_targets))
    if non_module_targets:
        errors.append("导航按钮必须指向课程模块：" + ", ".join(non_module_targets))
    if missing_module_buttons:
        errors.append("以下课程模块缺少导航按钮：" + ", ".join(missing_module_buttons))
    if duplicate_targets:
        errors.append("导航目标重复：" + ", ".join(duplicate_targets))
    if not parser.has_flow:
        errors.append("缺少数据流动画容器 ol.flow")
    if not parser.has_chat:
        errors.append("缺少组件对话 .chat")
    if not parser.has_term:
        errors.append("缺少术语提示 .term")

    for module_id, counts in parser.modules.items():
        if counts["source"] < 1:
            errors.append(f"模块 {module_id} 缺少带 data-source/data-lines 的真实代码块")
        if counts["code_pair"] < 1 or counts["plain_side"] < 1:
            errors.append(f"模块 {module_id} 缺少代码↔白话对照 .code-pair/.plain-side")
        if counts["quiz"] < 1:
            errors.append(f"模块 {module_id} 缺少 details.quiz")
    for block in parser.source_blocks:
        errors.extend(validate_source_block(block, repo))
    return errors


def existing_path(value: str, label: str) -> Path:
    path = Path(value).resolve()
    if not path.exists():
        raise argparse.ArgumentTypeError(f"{label}不存在：{value}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="kind", required=True)

    guide_parser = subparsers.add_parser("guide", help="Validate guide.md")
    guide_parser.add_argument("artifact")
    guide_parser.add_argument("repo")
    guide_parser.add_argument("--min-rows", type=int, default=1)
    guide_parser.add_argument("--json", action="store_true")

    course_parser = subparsers.add_parser("course", help="Validate course.html")
    course_parser.add_argument("artifact")
    course_parser.add_argument("repo")
    course_parser.add_argument("--min-modules", type=int, default=4)
    course_parser.add_argument("--max-modules", type=int, default=6)
    course_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    artifact = existing_path(args.artifact, "交付物")
    repo = existing_path(args.repo, "仓库")
    if not repo.is_dir():
        parser.error("仓库路径必须是目录")

    if args.kind == "guide":
        errors = validate_guide(artifact, repo, args.min_rows)
    else:
        errors = validate_course(
            artifact, repo, args.min_modules, args.max_modules
        )

    if errors:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "kind": args.kind,
                        "artifact": str(artifact),
                        "errors": errors,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1
        for error in errors:
            print(f"[ERROR] {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1
    if args.json:
        print(
            json.dumps(
                {"status": "pass", "kind": args.kind, "artifact": str(artifact)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    print(f"[OK] {args.kind} artifact is valid: {artifact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
