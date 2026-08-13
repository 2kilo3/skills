# Security Audit

Last reviewed: 2026-08-13

## Scope

This review covered all four skill directories, their scripts and bundled assets, the current worktree, and all seven reachable Git commits. The Office review inspected 21 reachable DOCX versions, including ZIP paths, relationships, active content, embedded objects, author properties, email addresses, and machine-specific paths.

The review combined manual data-flow and subprocess inspection with repository secret scans, Office archive scans, regression tests, environment checks, real DOCX generation and normalization, Microsoft Word PDF rendering, and visual inspection of the rendered pages.

## Findings and fixes

| Area | Finding | Resolution |
| --- | --- | --- |
| Git privacy | Reachable commits exposed personal author and committer email addresses. | Rebuilt all five reachable commits with the repository owner's GitHub noreply address while preserving names, dates, messages, and file trees apart from the separately documented DOCX cleanup. |
| DOCX privacy | Three bundled documents retained author/editor properties; one property contained an email address. | Cleared `creator` and `lastModifiedBy` in every reachable document version and updated all locked SHA-256 values. Other ZIP members were preserved byte-for-byte. |
| Office archives | The original scanner could miss directory symlinks, external OOXML relationships, active content, duplicate members, encryption, unsafe paths, and resource-exhaustion cases. | Added fail-closed checks for those cases, DTD/entity declarations, unsafe hyperlink schemes, member limits, uncompressed-size limits, and compression ratios. Ordinary `http`, `https`, and `mailto` hyperlinks remain allowed. |
| Document automation | DOCX files could reach Word or LibreOffice without the same checks used by the audit command. | Added pre-automation DOCX inspection, forced Office automation macros off, disabled link updates on open, and kept source documents read-only. Opaque legacy `.doc` conversion is limited to Microsoft Word with forced macro security. |
| Output paths | A predictable sibling temporary name and linkable output paths could overwrite an unintended file. | Replaced the predictable temporary file with a unique same-directory file and reject output paths whose final component or parent chain contains a symbolic link or junction. |
| Offline course | `course.html` validation covered only a narrow set of external URLs and did not require a strict browser policy. | Reject external resource-bearing attributes and embedding/navigation tags; require one exact offline CSP; reject meta refresh; require escaped source excerpts. |
| Repository inspection | Git status queries could invoke a repository-configured filesystem monitor. | Run bundled read-only Git preflight commands with `core.fsmonitor=false`. |
| Dependencies | Literature-note package compatibility was implicit. | Added bounded `python-docx` and `lxml` requirements and version-aware environment checks. |

## Verification

- Regression suite: 19 tests passed. Three real Windows symlink-creation subcases were skipped because the current account lacks the required privilege; mocked tests cover the same non-traversal and rejection branches.
- Python compilation: all scripts and tests compiled successfully under Python 3.12.13.
- Skill structure: all four skills passed the official OpenAI skill validator.
- Bundled security audits: all three scripted skill audits returned `status: pass`, including 35 inspected Office text members.
- Environment checks: project learning, Word Writer, and literature-note workflows reported ready in the review environment.
- Office history scan: 21 reachable DOCX versions inspected, with no remaining finding.
- End-to-end document checks: the locked literature template generated a valid 13-row note; Word Writer preserved paragraph, table, section, and image counts; the source rendered to one A4 page and the normalized copy to two A4 pages in Microsoft Word. Both passed visual inspection.

## Residual boundaries

No unresolved issue is known within the reviewed tree and history. This is not a proof that unknown vulnerabilities do not exist. Microsoft Word, LibreOffice, Python, Git, and installed dependencies remain trusted components. Real papers, documents, repositories, and generated outputs may contain private material even when the skill code is clean; review those inputs and outputs under their own disclosure rules.

The repository is licensed under the MIT License. The separate upstream MIT notice retained for `humanier-jf` must remain with redistributions.
