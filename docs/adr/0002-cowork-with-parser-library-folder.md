---
status: superseded by ADR-0003
---

# Runs in Cowork, with the Parser Library as a folder on disk

The skill runs in Claude Cowork. The Parser Library is a folder (shared within a firm) attached to a Cowork project, and Parsers run from it in place, so a Run costs only a command plus a short summary. We chose this over keeping Parsers in an artifact database (the pattern used by the dumpling-sauce skill) because every Run there would move parser code through the model's context.

## Considered Options

- **Artifact database as the Parser Library** (skill reads rows with `ArtifactData`). Proven in our own account, and doesn't need the desktop app, but each Statement Format costs about 2k tokens per conversation, and statements attached in chat may be read into context.
- **Standalone artifact app running parsers in the browser.** Zero-token Runs, but running stored code in the page is undocumented, and people outside the organisation can't write.

## Consequences

- Probe results (2026-10-29): Python 3.10 on Linux aarch64 with pdfplumber, pypdf, pypdfium2, pdfminer, pytesseract and the tesseract binary; pip reaches PyPI; files in the connected folder persist across tasks and scripts there run in place.
- Cowork re-materialises scripts bundled in a skill on every task (the model writes them out, costing output tokens). So the shared harness must be installed into the Parser Library folder once, not run from the skill folder.
- Each Cowork task runs as its own user and `/tmp` persists across tasks, so nothing may rely on fixed paths outside the connected folders.
- Not yet verified: a cloud-synced shared folder (Dropbox, OneDrive, Google Drive) as the Parser Library.
