# statement-parser

A Claude skill that turns bank and credit card statement PDFs into Xero bank statement CSVs that reconcile, while spending as few tokens as possible.

A bookkeeper attaches statements in Claude chat and gets back one CSV per account. A statement is written only if its opening balance plus its transactions equals its closing balance. The statement itself is never read into the conversation: a small Python Parser for its layout reads it in Claude's sandbox and prints summary lines only.

## How it works

- **Parsers.** Each printed layout (a Statement Format) has a generated Python Parser, run by a shared harness that handles reconciliation, dates, CSVs and duplicate warnings ([ADR-0001](docs/adr/0001-generated-parsers-in-shared-harness.md)).
- **Curated Parsers** ship with the skill, in [`parsers/curated/`](parsers/curated/): ANZ (Business Essentials, Business Advantage, Business Classic with Overdraft, Business One card), CommBank Business Transaction, NAB Business Everyday, Westpac Choice, American Express (two layouts), ING Orange Everyday and Macquarie Savings.
- **Build.** For a statement no Parser recognises, the skill offers to build one. It reads the statement once, writes a Parser, and checks it reconciles. The Leak Scan rejects any Parser that quotes the statement's account details or transactions.
- **Firm library.** Each firm has its own library, an artifact database where Parsers built by its bookkeepers are shared ([ADR-0003](docs/adr/0003-runs-in-cloud-shell-firm-parsers-in-artifact.md)). Each firm runs its own copy of the skill, the Firm Skill ([ADR-0004](docs/adr/0004-every-firm-runs-its-own-skill-copy.md)).
- **Promotion.** Asking to "promote our parsers" bundles the firm's Parsers into its Firm Skill, so they're no longer fetched from the library each time.

The vocabulary (Statement Format, Reconciliation, Firm Parser and so on) is defined in [GLOSSARY.md](GLOSSARY.md).

## Install

Build the skill zip:

```bash
python scripts/build_skill.py
```

Upload `dist/statement-parser.zip` in Claude under Customize › Skills. Then attach statement PDFs in a chat and ask for Xero CSVs.

To give a firm its own library and Firm Skill, ask the skill to "set up the statement parser". It creates the library and hands back a Firm Skill zip to upload in place of the original.

## Development

Tests run against synthetic statements and need Python 3.10 or later:

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
```

```bash
.venv/bin/pytest -q
```

The OCR test for scanned statements is skipped unless the `tesseract` binary is installed.

| Path | What's there |
|---|---|
| [`skill/`](skill/) | `SKILL.md` (what Claude follows), `BUILD.md` (the Parser contract) and the firm library page |
| [`harness/`](harness/) | The shared harness: `python -m harness run`, `detect`, `pages`, `check`, `leak-scan`, `firm-skill` |
| [`parsers/curated/`](parsers/curated/) | Curated Parsers, one per Statement Format |
| [`tests/`](tests/) | Tests at the harness's command line, with synthetic fixtures in `tests/fixtures/` |
| [`scripts/`](scripts/) | Packaging, and tools for redacting your own statements into private fixtures |
| [`docs/adr/`](docs/adr/) | Architecture decisions |

### Real statements

Never commit a statement or anything derived from one, even redacted. Keep them in `private/`, which git ignores. Fixtures redacted from your own statements with [`scripts/redact.py`](scripts/redact.py) go in `private/fixtures/curated/`, where [`tests/test_private_fixtures.py`](tests/test_private_fixtures.py) runs them when present.

## License

[MIT](LICENSE)
