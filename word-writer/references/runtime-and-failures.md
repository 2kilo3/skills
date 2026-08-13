# Runtime capability and failure handling

## Command convention

Set the working directory to the skill folder before running any command. In all examples, replace `<task-workdir>` with a writable directory belonging to the current task; do not create environments or outputs inside the installed skill.

Choose one interpreter command:

- Windows: `py -3`
- macOS/Linux: `python3`
- Host-bundled runtime: use its absolute Python path only after `scripts/check_environment.py` reports `core.status=ready`

Do not switch interpreters between preflight, normalization, audit and rendering.

## Capability levels

| Capability | Minimum requirement | If missing |
| --- | --- | --- |
| Audit/normalize DOCX | Python 3.10+, `python-docx`, `lxml` | blocked |
| Convert legacy DOC | LibreOffice or Microsoft Word | ask for DOCX or install converter |
| Render DOCX | LibreOffice or Microsoft Word | structural-only draft; visual QA blocked |
| Exact Chinese typography | SimHei/黑体 and Microsoft YaHei/微软雅黑 | install fonts or agree substitutes |
| Rasterize PDF pages | Installed document/PDF workflow, Poppler or equivalent | inspect PDF through another available renderer |

Run `scripts/check_environment.py` with every candidate Python interpreter. Choose the one whose JSON reports the core packages available. On Windows, use `python -X utf8` when a validator reads Chinese Markdown; this avoids locale-dependent GBK decoding failures.

## Fresh-computer sequence

1. Resolve the skill directory from the invoked skill; never hard-code a prior machine's absolute path.
2. Run the preflight with the selected interpreter.
3. If Python packages are missing, first try another already configured workspace interpreter. Install packages only with user authorization and in an isolated environment.
4. If fonts are missing, do not silently substitute. Structural work can continue, but rendered pages are not reproducible.
5. If conversion or rendering is missing, keep the source untouched and report the precise missing capability.

Use these installation commands only after approval. They install the compatible versions declared in `scripts/requirements.txt`, not into the system interpreter.

Windows:

```powershell
py -3 -m venv "<task-workdir>\.word-writer-venv"
"<task-workdir>\.word-writer-venv\Scripts\python.exe" -m pip install -r "scripts\requirements.txt"
```

macOS/Linux:

```sh
python3 -m venv "<task-workdir>/.word-writer-venv"
"<task-workdir>/.word-writer-venv/bin/python" -m pip install -r "scripts/requirements.txt"
```

Run the preflight again with the virtual environment's Python. Do not continue if installation fails or the report still says `core.status=blocked`.

## Failure matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: docx` | Wrong interpreter or missing `python-docx` | switch interpreter; otherwise install dependency |
| `.doc` cannot convert | Microsoft Word unavailable or input is not trusted | request a `.docx` produced in a trusted environment; do not automate opaque `.doc` through LibreOffice |
| audit reports nonstandard fonts | unnormalized OOXML story or newly edited output | normalize again, then audit the exact final file |
| rendered CJK glyphs differ | fonts missing/substituted | install required fonts and re-render |
| footer contains extra text | source footer not fully cleared or later edit reintroduced it | normalize exact final file again |
| images disappear | toolchain damaged relationships/content | stop, restore source copy, use a preservation-capable editor |
| output already exists | unsafe overwrite attempt | select a new name or obtain explicit overwrite authorization and use `--force` |
| audit passes but layout clips | structural checks cannot detect pagination | correct layout and repeat audit + render |
| security audit reports findings or warnings | credential, private path, suspicious file, symlink or uninspected binary | stop distribution; remove accidental material or complete a manual provenance review, then rerun |

## Resource-limited behavior

For long documents, keep the same correctness gates but reduce context load: obtain a structural inventory first, normalize in one pass, and inspect rendered pages in batches. Do not sample pages for final acceptance; every page must still be viewed. Avoid repeated full-document rewrites when only one localized content edit is requested.

Do not copy passwords, cookies, API keys or access tokens into temporary scripts, logs, examples or skill assets. Keep required authentication in an approved secret store or environment variable and record only the variable name. Before publishing the skill, run `scripts/audit_skill_security.py`; scan the task directory with `--root` when the output is expected to be credential-free.
