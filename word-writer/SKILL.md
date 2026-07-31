---
name: word-writer
description: Create, edit, or normalize professional Microsoft Word documents in `.doc` or `.docx` using a strict Chinese formatting standard: black document text, SimHei headings, Microsoft YaHei body text, black-grid white-fill tables with centered bold header rows, blank headers, and centered page-number-only footers. Use for new Word authoring, legacy `.doc` conversion, formatting cleanup, handbook/report delivery, or when a user asks for standardized Word typography, tables, headers, footers, or page numbers.
---

# Word Writer

Apply the user's Word formatting standard deterministically while preserving document content and expressive figure colors.

## Required standard

Read [references/style-spec.md](references/style-spec.md) before creating or normalizing a document. Treat it as the design authority.

## Workflow

1. Preserve the source file. Write a new deliverable unless the user explicitly requests in-place editing.
2. For an existing `.doc` or `.docx`, run `scripts/normalize_word.py`. The script accepts legacy `.doc` when LibreOffice or Microsoft Word conversion is available.
3. For a new document, configure the required styles, tables, headers, and footers before drafting. Run the normalizer afterward as an enforcement pass.
4. Keep diagrams and figures expressive. Do not convert images to grayscale or recolor embedded visuals merely to match the black-text rule.
5. Run the script's structural audit and require `status: pass`.
6. Render the final DOCX to page images with the installed document-render workflow. Inspect every page for clipping, overlap, broken tables, font substitution, missing glyphs, and footer placement. If LibreOffice is unavailable on Windows, render through Microsoft Word to PDF and rasterize the PDF for the same page-by-page review.
7. Re-run normalization and rendering after any layout-sensitive correction.

## Normalize an existing document

Use the workspace-bundled Python runtime:

```powershell
python scripts/normalize_word.py input.docx --output output.docx --page-numbers preserve
python scripts/normalize_word.py input.doc --output output.docx --page-numbers preserve
```

Page-number modes:

- `preserve`: keep page numbers only when the source already has them; normalize them to a centered, black, page-number-only footer.
- `always`: add centered page numbers. Omit the first-page number when the document already uses a distinct first-page header/footer.
- `none`: leave every footer blank.

Use `--audit-only` for a read-only conformance check:

```powershell
python scripts/normalize_word.py output.docx --audit-only
```

## Creation rules

- Use real Word paragraph styles for Title, Subtitle, and Heading 1-9.
- Use real tables for tabular data and real numbering definitions for lists.
- Keep body text readable; do not reduce font size merely to force content onto fewer pages.
- Use tables only for genuinely row/column data. Do not package ordinary prose in decorative one-cell tables unless the source already relies on them and the user asks only for normalization.
- Keep headers empty. A footer may contain only a centered page-number field.
- Preserve link targets and interaction structures. Display hyperlink text in black; underline may remain.

## Validation contract

Do not declare success until:

- the skill folder passes `quick_validate.py`;
- the formatter has been tested on at least one representative DOCX;
- both output documents pass structural audit;
- every rendered page has been visually inspected;
- the final diff or content inventory shows that no requested content or figure was lost.
