# 10: Skill v0: sealed Runs with Bundled Parsers in Claude chat

**What to build:** The first time the work runs in the real Claude app: `SKILL.md` plus the bundled harness and Parsers, packaged as an uploadable skill (ADR-0003). Kept as early as possible because this is the first contact with the real platform.

Spec stories: 1, 7, 23, 27.

**Blocked by:** 02: PDF statements as input; 04: Detection by Signature; 07: Batch output

**Status:** done

- [x] In a real chat, the attached statements are passed to the harness by path without being opened (checked in the conversation)
- [x] The harness and Bundled Parsers run in place from the skill's own files, so the model writes no scripts out
- [x] The summary is relayed and the CSVs are handed back as downloads
- [x] A manual scenario check is written down and passed

## Comments

- 2026-10-29: Skill packaged. `python scripts/build_skill.py --demo` writes `dist/statement-parser.zip` (SKILL.md, harness, Curated Parsers, plus the synthetic Probe Bank Parser) and `dist/demo-statement.pdf`. Automated test: the unzipped skill runs its bundled Parser from its own folder. The criteria above need the manual check in a real Claude chat: upload the zip, attach the demo statement, ask for a Xero CSV.
- 2026-10-29: Manual check passed in Claude chat. A real statement from an unsupported bank came back BUILD without being opened; the demo statement came back PASS with `Probe-Bank-DEP-xx5678-2026-03.csv` handed back as a download, identical to the CSV the tests expect.
