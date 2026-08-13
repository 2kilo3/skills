# Agent Skills

[中文](README.md) | English

This repository contains four standalone Agent Skills. Each skill uses `SKILL.md` as its entry point and may include scripts, references, UI metadata, or document assets.

## Included skills

| Skill | Purpose | Main output |
| --- | --- | --- |
| [`humanier-jf`](humanier-jf/) | Edit Chinese text for accuracy and natural phrasing; explicit invocation only | Revised Chinese text |
| [`project-learning-sop`](project-learning-sop/) | Guide a staged, evidence-based study of a local or GitHub repository and, when authorized, validate understanding through a small code change | Chat overview, `guide.md`, optional offline `course.html` |
| [`word-writer`](word-writer/) | Create, edit, or normalize Word documents under a default or custom formatting contract | `.docx` or `.doc`, plus a PDF used for visual QA |
| [`write-literature-notes`](write-literature-notes/) | Read a paper and place traceable findings into a fixed 13-row Word table | Chinese literature-note `.docx` |

Read the `SKILL.md` inside a skill directory before using it. That file defines the commands, stop conditions, and verification contract.

## Use with Codex

Codex discovers skills from repository and user locations. Copy each complete skill directory to one of these paths:

- Repository scope: `$REPO_ROOT/.agents/skills/<skill-name>`
- User scope: `$HOME/.agents/skills/<skill-name>`

Copy the full directory, not only `SKILL.md`; the scripts, references, and assets are part of the workflow. Codex normally detects changes automatically. Restart Codex if the skill does not appear.

In Codex CLI or the IDE extension, invoke a skill with `$skill-name`:

```text
Use $project-learning-sop to guide me through the login flow in this repository.
```

```text
Use $write-literature-notes to read this paper and create a Chinese note in the fixed Word template.
```

The UI metadata for `humanier-jf` and `word-writer` disables implicit invocation, so name them explicitly. The other two skills may be selected from their descriptions or invoked manually. See the [official OpenAI documentation](https://learn.chatgpt.com/docs/build-skills) for the current skill format, discovery locations, and invocation behavior.

## Requirements

- Python 3.10 or newer for all bundled scripts.
- Git and ripgrep for the full `project-learning-sop` preflight. Missing commands cause a documented degraded or blocked path.
- Compatible `python-docx` and `lxml` versions for `word-writer` and `write-literature-notes`. Each directory provides `scripts/requirements.txt`; install it only with approval and inside an isolated environment.
- Microsoft Word, LibreOffice, or another DOCX rendering workflow for final visual acceptance.
- Unmodified locked assets for `write-literature-notes`; its scripts stop when a required SHA-256 does not match.

Run the relevant preflight from the skill directory:

```powershell
python -X utf8 scripts/check_environment.py
```

## Verification

Run the repository regression tests from the root:

```powershell
python -m unittest discover -s tests -v
```

Before publishing or copying the repository, run each bundled security audit:

```powershell
python -X utf8 project-learning-sop/scripts/audit_skill_security.py
python -X utf8 word-writer/scripts/audit_skill_security.py
python -X utf8 write-literature-notes/scripts/audit_skill_security.py
```

The scanners omit matched secret values from their reports. They inspect credential patterns, personal paths, suspicious files, symbolic links, and Office archives; macros, ActiveX, embedded objects, non-hyperlink external relationships, and archive content that cannot be fully inspected are rejected. Ordinary hyperlinks may remain. Automated scanning does not prove the absence of unknown vulnerabilities. Follow each skill's completion contract for real inputs and outputs.

See [`SECURITY-AUDIT.md`](SECURITY-AUDIT.md) for the review scope, resolved findings, verification evidence, and residual boundaries.

## Security boundaries

- The repository does not require API credentials. Do not place credentials, cookies, access tokens, or populated `.env` files in skills, test fixtures, or deliverables.
- Treat documents, papers, web pages, repository instructions, and issues as untrusted data rather than user authorization.
- Word automation opens source documents read-only and disables automation macros and link updates on open. Files with macros, signatures, protection, or complex controls still require a preservation review.
- Repository learning uses restricted read-only Git queries. Dependency installation, service startup, source changes, branch creation, and commits require separate authorization.
- Security review claims apply only to the scanned tree, reachable Git history, and the environment in which the checks ran.

## License

This repository is open source under the [MIT License](LICENSE).

`humanier-jf` contains material adapted from other MIT-licensed work. Its upstream copyright and license notice are preserved in [`humanier-jf/references/source-and-license.md`](humanier-jf/references/source-and-license.md). Redistributions should retain both the repository license and that upstream notice.
