---
name: word-writer
description: "Create, edit, or normalize professional Microsoft Word `.doc` and `.docx` documents using a strict Chinese formatting standard: black document text, SimHei headings, Microsoft YaHei body text, black-grid white-fill tables with centered bold header rows, blank headers, and centered page-number-only footers. Use for Word authoring, legacy DOC conversion, formatting cleanup, handbook/report delivery, or standardized typography, tables, headers, footers, and page numbers."
---

# Word Writer SOP

Apply one deterministic Word style contract while preserving requested content, document structure, links, fields and expressive figure colors.

## Design authority and scope

Read `references/style-spec.md` completely before touching a document. Treat it as the only formatting authority unless the user supplies a more specific template. When a domain skill owns a fixed template, such as `write-literature-notes`, that template takes precedence; do not run this normalizer if it would erase required template styling.

Normalize copies by default. Never treat a request to “edit” as permission to overwrite the only source copy.

## SOP

### 0. Preflight and classify the task

1. Classify the operation as new authoring, content edit, format normalization, legacy `.doc` conversion, or audit-only.
2. Record the source path, output path, page-number mode and user-required content changes. Keep source and output paths different during processing.
3. Run:

```powershell
python -X utf8 scripts/check_environment.py
```

Use an interpreter that reports `core.status=ready`. Do not assume the application-bundled Python or system Python has the required packages. Read `references/runtime-and-failures.md` for `degraded` and `blocked` outcomes.

### 1. Establish a preservation baseline

Before editing, inventory paragraph text, table count and dimensions, images, hyperlinks, sections, fields, bookmarks and content controls. Record the source SHA-256. For format-only work, this inventory is the preservation contract; for content edits, record exactly which items may change.

### 2. Author or edit

- **Existing `.docx`**: make requested content edits in a new working copy, then normalize it.
- **Legacy `.doc`**: let the normalizer convert through LibreOffice or Microsoft Word. If neither is available, stop and request a `.docx` source or an installed converter.
- **New document**: create real Word paragraph styles, real tables and real list numbering. Draft at readable sizes, then use the normalizer as the enforcement pass.
- **In-place request**: still generate and validate a sibling temporary output first. Preserve a recoverable backup before replacing the original.

Do not recolor embedded figures, flatten links, rebuild fields as plain text, or use one-cell tables to imitate ordinary prose.

### 3. Normalize

```powershell
python -X utf8 scripts/normalize_word.py input.docx `
  --output output.docx --page-numbers preserve
```

Page-number modes:

- `preserve`: retain page numbers only when the source already has them, normalized to a centered page-number-only footer.
- `always`: add centered page numbers; preserve a deliberately blank distinct first page.
- `none`: leave all footers blank.

The command refuses identical input/output paths and existing outputs. Use a new path, or add `--force` only after the user has authorized overwriting that exact output file.

### 4. Structural audit

Require the normalization report to contain `status: pass`. Re-run a read-only audit against the exact final DOCX:

```powershell
python -X utf8 scripts/normalize_word.py output.docx --audit-only
```

Compare the final content inventory with the baseline. A passing style audit does not prove content preservation; both checks are required.

### 5. Render and inspect every page

```powershell
python -X utf8 scripts/render_docx.py output.docx --pdf preview.pdf
```

Render the PDF to page images with the available document/PDF workflow. Inspect every page for clipping, overlap, broken tables, fixed-height truncation, font substitution, missing glyphs, unexpected blank pages, figure loss and footer placement. Re-run normalization, audit and rendering after any layout-sensitive correction.

If no renderer is available, structural normalization may be delivered only as an unverified draft; do not claim completion.

### 6. Security review

Before delivery, publishing, or copying this skill, run:

```powershell
python -X utf8 scripts/audit_skill_security.py
```

Require `status: pass`, with empty `findings` and `warnings`. The scanner checks text and OOXML archive contents without echoing matched values. Also scan the task-specific working/output directory with `--root` when the deliverable is expected to be credential-free. If a requested document intentionally contains sensitive content, do not silently remove it; stop before external sharing and confirm the intended audience. Remove accidental credentials and private paths, rotate any live credential that may have been exposed, then rerun the scan.

### 7. Deliver

Deliver the final file only after the audit, inventory comparison and visual inspection all refer to the same unchanged output. Report what content was intentionally changed, the page-number mode, the audit result and any limitation that could not be tested.

## Exception rules

- Missing `python-docx` or `lxml`: select another Python environment or install the packages; do not reimplement OOXML ad hoc.
- Missing SimHei or Microsoft YaHei: normalization can set font names, but rendered appearance is not reproducible. Install the fonts or obtain approval for substitutes before final delivery.
- Password-protected, corrupted or rights-managed input: stop and request an accessible copy; do not bypass protection.
- Macros, signatures, tracked changes or complex content controls: save to a copy and verify preservation explicitly; if the toolchain cannot preserve them, stop rather than flattening them.
- Dirty or user-modified source/output directory: never remove unrelated files; choose a distinct deliverable path.
- Source contains deliberately colored Word text that the user wants to keep: resolve this direct conflict with the black-text contract before normalization.
- Security scan reports a credential, private user path, suspicious credential file or uninspected binary: do not publish or copy the skill; remove the accidental material or complete a documented manual provenance review, then rerun.

## Completion contract

Do not report completion until the skill structure validates, a representative DOCX has been normalized, the exact final output passes `--audit-only`, content/figure inventory matches the authorized change set, every rendered page has been inspected, and the final skill security scan reports `status: pass`. Report any check that could not be performed as a blocker to final visual or security acceptance.

## Resources

- `references/style-spec.md`: typography, table, header/footer, figure and preservation rules.
- `references/runtime-and-failures.md`: fresh-computer capability matrix and fallbacks.
- `scripts/check_environment.py`: package, font, conversion and rendering preflight.
- `scripts/normalize_word.py`: normalization and structural audit.
- `scripts/render_docx.py`: deterministic LibreOffice/Word PDF renderer selection.
- `scripts/audit_skill_security.py`: redacted credential, private-path and archive-content scan.
