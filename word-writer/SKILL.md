---
name: word-writer
description: "Manually invoked workflow for creating, editing, or normalizing professional Microsoft Word `.doc` and `.docx` documents. Supports the built-in Chinese formatting standard or an interactive custom typography profile for heading/body fonts and sizes plus page-number settings. Invoke only through explicit `$word-writer` selection; do not activate it implicitly."
---

# Word Writer SOP

Apply a confirmed Word style contract while preserving requested content, document structure, links, fields and expressive figure colors.

## Required startup interaction

Run this skill only after the user explicitly invokes `$word-writer`. Before running document commands or modifying files, determine the mode from the user's message. If the user has not already selected a mode, ask exactly one blocking question:

```text
请选择排版模式：
1. 默认规范（当前模式：标题黑体、正文微软雅黑、黑色文字、标准表格、空白页眉、居中页码）
2. 自定义排版（可设置标题/正文字体与字号、页码模式和页码字号）
```

- **Default mode**: proceed with the existing style contract without asking typography questions.
- **Custom mode**: collect all missing choices in one compact prompt: heading font, heading size in points, body font, body size in points, page-number mode (`preserve`, `always`, or `none`), and page-number size. Allow blank sizes only for an existing document, where blank means preserve source sizes. Require explicit sizes for a new document.
- Treat unspecified custom fields as the current defaults: SimHei/黑体 headings, Microsoft YaHei/微软雅黑 body text, preserved source heading/body sizes, `preserve` page-number mode, and 10 pt page numbers.
- Keep the standard table, black-text and blank-header rules in both modes. If the user requests other table, color, or header rules, record them as explicit exceptions and do not let the normalizer silently undo them.
- Do not repeat questions for choices already present in the invocation. Summarize the resolved profile before processing and ask only when a value is ambiguous or conflicts with the document.

## Design authority and scope

Read `references/style-spec.md` completely before touching a document. In default mode, treat it as the formatting authority unless the user supplies a more specific template. In custom mode, the confirmed typography and page-number choices override only the corresponding defaults; all other rules remain in force. When a domain skill owns a fixed template, such as `write-literature-notes`, that template takes precedence; do not run this normalizer if it would erase required template styling.

Normalize copies by default. Never treat a request to “edit” as permission to overwrite the only source copy.

## SOP

### 0. Preflight and classify the task

1. Classify the operation as new authoring, content edit, format normalization, legacy `.doc` conversion, or audit-only.
2. Record the selected mode, resolved style profile, source path, output path, page-number mode and user-required content changes. Keep source and output paths different during processing.
3. Set the working directory to this skill folder, the directory containing this `SKILL.md`. Resolve it from the invoked skill; never hard-code a path from another machine.
4. Select one Python 3.10+ interpreter and use it for every command. On Windows try `py -3`; on macOS/Linux try `python3`; otherwise use a host-provided Python only after it passes the preflight.
5. Run the following command after replacing `<python>` with the selected command:

```text
<python> -X utf8 scripts/check_environment.py
```

Use an interpreter that reports `core.status=ready`. Do not assume the application-bundled Python or system Python has the required packages. If packages are missing, read `references/runtime-and-failures.md`, obtain permission before installing anything, create an isolated environment in the task workspace, and install `scripts/requirements.txt`. Follow the same reference for `degraded` and `blocked` outcomes.

### 1. Establish a preservation baseline

Before editing, inventory paragraph text, table count and dimensions, images, hyperlinks, sections, fields, bookmarks and content controls. Record the source SHA-256. For format-only work, this inventory is the preservation contract; for content edits, record exactly which items may change.

### 2. Author or edit

- **Existing `.docx`**: make requested content edits in a new working copy, then normalize it.
- **Legacy `.doc`**: convert only through Microsoft Word with forced macro security. If Word is unavailable, request a `.docx` source created in a trusted environment; the workflow does not pass opaque `.doc` files to LibreOffice automation.
- **New document**: create real Word paragraph styles, real tables and real list numbering. Draft at readable sizes, then use the normalizer as the enforcement pass.
- **In-place request**: still generate and validate a sibling temporary output first. Preserve a recoverable backup before replacing the original.

Do not recolor embedded figures, flatten links, rebuild fields as plain text, or use one-cell tables to imitate ordinary prose.

### 3. Normalize

```text
<python> -X utf8 scripts/normalize_word.py "input.docx" --output "output.docx" --page-numbers preserve
```

Page-number modes:

- `preserve`: retain page numbers only when the source already has them, normalized to a centered page-number-only footer.
- `always`: add centered page numbers; preserve a deliberately blank distinct first page.
- `none`: leave all footers blank.

The command refuses identical input/output paths and existing outputs. Use a new path, or add `--force` only after the user has authorized overwriting that exact output file.

For custom mode, add the confirmed typography arguments. Font arguments set the same selected name in Latin, complex-script and East Asian font slots. Omit a heading or body size only when preserving the existing size is intentional.

```text
<python> -X utf8 scripts/normalize_word.py "input.docx" --output "output.docx" --page-numbers always --heading-font "方正小标宋简体" --heading-size 18 --body-font "仿宋_GB2312" --body-size 12 --page-number-size 10
```

### 4. Structural audit

Require the normalization report to contain `status: pass`. Re-run a read-only audit against the exact final DOCX:

```text
<python> -X utf8 scripts/normalize_word.py "output.docx" --audit-only
```

In custom mode, pass the exact same `--heading-font`, `--heading-size`, `--body-font`, `--body-size`, and `--page-number-size` values to `--audit-only`. A custom document audited without its profile is not a valid check.

Compare the final content inventory with the baseline. A passing style audit does not prove content preservation; both checks are required.

### 5. Render and inspect every page

```text
<python> -X utf8 scripts/render_docx.py "output.docx" --pdf "preview.pdf"
```

Render the PDF to page images with the available document/PDF workflow. Inspect every page for clipping, overlap, broken tables, fixed-height truncation, font substitution, missing glyphs, unexpected blank pages, figure loss and footer placement. Re-run normalization, audit and rendering after any layout-sensitive correction.

If no renderer is available, structural normalization may be delivered only as an unverified draft; do not claim completion.

### 6. Security review

Before delivery, publishing, or copying this skill, run:

```text
<python> -X utf8 scripts/audit_skill_security.py
```

Require `status: pass`, with empty `findings` and `warnings`. The scanner checks text and OOXML archive contents without echoing matched values. Also scan the task-specific working/output directory with `--root` when the deliverable is expected to be credential-free. If a requested document intentionally contains sensitive content, do not silently remove it; stop before external sharing and confirm the intended audience. Remove accidental credentials and private paths, rotate any live credential that may have been exposed, then rerun the scan.

### 7. Deliver

Deliver the final file only after the audit, inventory comparison and visual inspection all refer to the same unchanged output. Report what content was intentionally changed, the page-number mode, the audit result and any limitation that could not be tested.

## Exception rules

- Missing `python-docx` or `lxml`: select another Python environment or install the packages; do not reimplement OOXML ad hoc.
- Missing a selected default or custom font: normalization can set font names, but rendered appearance is not reproducible. Install the font or obtain approval for a substitute before final delivery.
- Password-protected, corrupted or rights-managed input: stop and request an accessible copy; do not bypass protection.
- Macros, signatures, tracked changes or complex content controls: save to a copy and verify preservation explicitly; if the toolchain cannot preserve them, stop rather than flattening them.
- Dirty or user-modified source/output directory: never remove unrelated files; choose a distinct deliverable path.
- Source contains deliberately colored Word text that the user wants to keep: resolve this direct conflict with the black-text contract before normalization.
- Security scan reports a credential, private user path, suspicious credential file or uninspected binary: do not publish or copy the skill; remove the accidental material or complete a documented manual provenance review, then rerun.

## Completion contract

Do not report completion until the skill structure validates, a representative DOCX has been normalized with the confirmed mode/profile, the exact final output passes `--audit-only` with that same profile, content/figure inventory matches the authorized change set, every rendered page has been inspected, and the final skill security scan reports `status: pass`. Report any check that could not be performed as a blocker to final visual or security acceptance.

## Resources

- `references/style-spec.md`: typography, table, header/footer, figure and preservation rules.
- `references/runtime-and-failures.md`: fresh-computer capability matrix and fallbacks.
- `scripts/check_environment.py`: package, font, conversion and rendering preflight.
- `scripts/requirements.txt`: pinned Python packages for an isolated fresh-computer environment.
- `scripts/normalize_word.py`: normalization and structural audit.
- `scripts/render_docx.py`: deterministic LibreOffice/Word PDF renderer selection.
- `scripts/audit_skill_security.py`: redacted credential, private-path and archive-content scan.
