# Word formatting specification

## Typography

| Role | Font | Color | Weight |
|---|---|---|---|
| Title, Subtitle, Heading 1-9, custom heading styles | SimHei / 黑体 | `#000000` | Preserve the document's hierarchy; headings may remain bold |
| Body, lists, captions, notes, hyperlinks, table text | Microsoft YaHei / 微软雅黑 | `#000000` | Preserve meaningful bold/italic emphasis |
| Page number | Microsoft YaHei / 微软雅黑 | `#000000` | Normal |

Apply the font to Latin, complex-script, and East Asian font slots. Remove theme-font and theme-color overrides that could reintroduce a different appearance. Hyperlinks may remain underlined but must not remain blue or another color.

## Tables

- Use white cell fill (`#FFFFFF`) throughout.
- Use single black borders (`#000000`) on the outside and all internal grid lines.
- Use a 1 pt border unless the source requires a heavier border for legibility.
- Mark the first row as a repeating header row.
- Center the first-row text horizontally and vertically.
- Make every first-row text run bold.
- Vertically center all other cells. Choose body-cell horizontal alignment according to content.
- Use sufficient cell padding; default to 80 DXA top/bottom and 120 DXA start/end.
- Never use a fixed row height that can clip wrapped content.

## Headers and footers

- Keep all headers empty, including first-page and even-page variants.
- Keep footers empty unless page numbers are used.
- When used, the footer must contain only a centered `PAGE` field.
- Format the page number as black, 10 pt Microsoft YaHei.
- Do not add document names, dates, rules, labels, confidentiality notes, or other small text.
- Preserve a deliberately blank first-page footer when the source uses a distinct first page.

## Figures

- Preserve existing images, diagrams, charts, and their color palettes.
- Use color intentionally when creating new figures so relationships and states are easy to distinguish.
- Keep figure labels legible and ensure the figure fits within the page without clipping.
- The black-text requirement governs Word text, not text already rasterized inside an embedded image.

## Content preservation

- Preserve paragraph text, table data, hyperlinks, bookmarks, fields, content controls, images, captions, and section order unless the user asks for content changes.
- Treat formatting normalization as a surgical edit, not a rewrite.
- Save a new output file by default.

