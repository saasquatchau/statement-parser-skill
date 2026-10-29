---
name: statement-parser
description: Turns bank and credit card statement PDFs into Xero bank statement CSVs that reconcile, and manages the firm's statement Parsers. Use whenever bank or credit card statement PDFs are attached, and when the bookkeeper asks to set up the statement parser, build a Parser for a bank, or "promote our parsers". Load this skill before doing anything with an attached statement: never open, read or extract a statement PDF yourself, not even to see what it is, since statements stay unread.
---

# Statement Parser

Turn attached statement PDFs into Xero CSVs using this skill's bundled harness. The harness picks a Parser for each statement, checks that the opening balance plus the transactions equals the closing balance (Reconciliation), and writes the CSVs. A statement that doesn't reconcile is never written.

## Rules

- **Statements are sealed.** Never open, read, extract, OCR or print an attached statement yourself, and never read the harness or Parser source files. Pass statement file paths to the harness and work only from what it prints. This keeps client data and tokens out of the conversation. The one exception is a Build the bookkeeper has agreed to, which reads pages through `harness pages` only.
- Show the bookkeeper the harness's summary lines; they are safe. Never paste statement content, and never comment on the transactions (what they might be, whether they look odd): the bookkeeper knows the client.
- Don't retry a failed statement with a different approach or "fix" the numbers. Report the failure.
- Never add `--format` yourself: it is only for re-running with the Statement Format the bookkeeper picked from an `ASK` line. A `BUILD` or `FAIL` is answered by offering a Build, not by trying other Parsers.

## Run

1. From this skill's folder (the folder containing this SKILL.md; if unsure, `dirname "$(find / -name SKILL.md -path '*statement-parser*' 2>/dev/null | head -1)"`), run every attached statement in one command, without listing them first:

   ```
   cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness run /mnt/user-data/uploads/* --parsers parsers/curated --parsers parsers/promoted --out /mnt/user-data/outputs
   ```

   If the bookkeeper names only some attachments, pass just those paths instead. Add `--per-statement` only if the bookkeeper asks for one CSV per statement instead of one per account.
2. **Firm Parsers.** If the output ends with a `NEXT` line, do this before replying to the bookkeeper; it is not optional, and a `FAIL` or `BUILD` isn't final until it's done:
   1. With the claude-artifacts database tools, list the `parsers` collection of the library named on the `NEXT` line. Each row is one Firm Parser's metadata; the code is not in it.
   2. In one command, write the rows as a JSON list of `{"id", "statement_format", "signature"}` (the row's document id, and its `statement_format` and `signature` fields) and detect:

      ```
      mkdir -p /tmp/sp/firm && cat > /tmp/sp/signatures.json <<'JSON'
      <the JSON list>
      JSON
      cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness detect <the BUILD/FAIL statement paths...> --signatures /tmp/sp/signatures.json
      ```

   3. For each id on a `FETCH` line, get document `source` from collection `parsers/<id>/files` and write its `code` field, exactly as stored, to `/tmp/sp/firm/<id>.py`. Fetch each Parser once per conversation; reuse files already in `/tmp/sp/firm`.
   4. In one command, delete the first run's CSVs and re-run the whole batch with the Firm Parsers:

      ```
      rm -f /mnt/user-data/outputs/*.csv && cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness run /mnt/user-data/uploads/* --parsers parsers/curated --parsers parsers/promoted --firm-parsers /tmp/sp/firm --out /mnt/user-data/outputs
      ```

      (with the same statement paths and options as step 1). Use this second run's output from here on.
3. Read the output. Each line starts with a status:
   - `PASS` the statement reconciled. Pass on any warning after `;` (dates outside the period, scanned/OCR: check balances).
   - `FAIL` the statement was left out; say which check failed, as printed. If a Parser that matched it failed (possibly the bank redesigned its statement), offer a Build (below); never start one unasked.
   - `ASK` several Parsers match. Ask the bookkeeper which Statement Format it is, then re-run just that statement with `--format "<their choice>"`.
   - `BUILD` no Parser exists for this statement yet. If this skill's folder has a `firm.json`, offer a Build (below). If not, explain that the firm needs Setup (below) before it can build and keep its own Parsers, and offer that.
   - `CSV` a file was written to /mnt/user-data/outputs. Share each one with the bookkeeper as a download.
   - `WARN` possible duplicate rows in that CSV; pass it on word for word, with nothing added.
   - `NEXT` an instruction for you (step 2), not for the bookkeeper. It never appears in the output you report from.
   - `TIP` Firm Parsers were used. Pass it on word for word, once per conversation.
4. Reply briefly: one line per statement, the CSV downloads, and any warnings. Bookkeepers know Xero: don't explain how to import.

## Build (a new Firm Parser)

A Build is the only time a statement is read, and the only expensive step. Never start one without the bookkeeper's yes.

1. Ask first, naming the statement: "There's no Parser for <file> yet. Build one? I'll read the statement once to learn its layout, which costs about 20–40k tokens; after that, statements like it cost almost nothing." Wait for a yes.
2. Read `BUILD.md` in this skill's folder.
3. Print the pages you need from one statement of that format (default first and last page; add `--pages 2,3` etc. only if needed):

   ```
   cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness pages <statement path>
   ```

   If rows leave the unused Debits or Credits column empty (see "Empty columns" in `BUILD.md`), print the pages again with `--columns "<debit heading>,<credit heading>"`, headings exactly as printed, to see the tagged text the Parser will read.

4. Write the Parser to `/tmp/sp/build/<id>.py`, where `<id>` is short, lowercase with underscores, and names the issuer and product (e.g. `anz_credit_card`).
5. Check it against every statement in the batch that didn't reconcile, and against the library's Signatures (`/tmp/sp/signatures.json` from the Firm Parsers step):

   ```
   cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness check /tmp/sp/build/<id>.py <statement paths...> --signatures /tmp/sp/signatures.json
   ```

   - `REJECT` fix the Parser at the same path and check again. When the line says "stop and report", stop: tell the bookkeeper the Build didn't succeed and which check failed. Nothing is saved.
   - `EXISTS` a colleague already built this format. Fetch that Parser as in Firm Parsers step 3 and re-run instead.
   - `ACCEPT` followed by `ROW` with the library row. Go on.
6. Save it to the library with the claude-artifacts database tools: create document `<id>` in collection `parsers` with the `ROW` fields except `id`, plus `built` (today, YYYY-MM-DD) and `promoted_in` (null); then create document `source` in collection `parsers/<id>/files` with field `code` set to the file's exact contents. Only create, never overwrite: if `<id>` already exists, a colleague saved first, so fetch and use theirs.
7. Copy the file to `/tmp/sp/firm/<id>.py` and re-run the whole batch with `--firm-parsers /tmp/sp/firm` (as in Firm Parsers step 4). Report as usual, adding that the new Parser is saved in the firm's library for everyone in the firm.

## Promotion (bundling Firm Parsers into the Firm Skill)

Promotion makes the firm's Parsers free to use: they're bundled into the Firm Skill instead of fetched from the library each conversation. Run it only when the bookkeeper asks ("promote our parsers"). If this skill's folder has no `firm.json`, the firm needs Setup first.

1. List the library's `parsers` collection (library link in `firm.json`). For every row whose id isn't already a file under this skill's `parsers/` folders (`ls parsers/*/`), get document `source` from `parsers/<id>/files` and write its `code` field, exactly as stored, to `/tmp/sp/promote/<id>.py`.
2. Rebuild the Firm Skill. Parsers it already bundles are kept automatically:

   ```
   cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness firm-skill --promote /tmp/sp/promote --out /mnt/user-data/outputs
   ```

   - `REJECT` a Parser contains a long number that could be an account number. Nothing was promoted; tell the bookkeeper which Parser, and that it needs rebuilding before it can be promoted.
   - `SKILL` then `PROMOTED`. For each id on the `PROMOTED` line, update its row in `parsers` to set `promoted_in` to the version printed (e.g. `"v2"`).
3. Share `statement-parser.skill` as a download, with steps: download it; in Customize › Skills remove the current "statement-parser" and upload the file; start a new chat. The Parsers stay in the library, so nothing is lost if the skill is ever reinstalled; promoting again bundles them back.

## Setup (first use by a firm)

Run Setup only when the bookkeeper asks for it, or accepts it when offered. It gives the firm its own library for Firm Parsers and its own copy of this skill (the Firm Skill) that knows where that library is. If `firm.json` already exists in this skill's folder, the firm is set up: say so and show its library link from that file instead.

1. Ask for the firm's name.
2. Create the library. Use the claude-artifacts tools (look up their schemas first if they aren't loaded): read `library/index.html` from this skill's folder (the only skill file Setup reads) and publish it as a new artifact titled "<firm name> Statement Parser Library" with the database capability declared. Follow the tools' own instructions on declaring capabilities. Note the artifact's claude.ai link.
3. Build the Firm Skill:

   ```
   cd <this skill's folder> && PYTHONDONTWRITEBYTECODE=1 python3 -m harness firm-skill --library "<library link>" --firm "<firm name>" --out /mnt/user-data/outputs
   ```

   It prints `SKILL statement-parser.skill: …` when done, or `FAIL` if the link isn't a claude.ai artifact link.
4. Share `statement-parser.skill` as a download and give these steps, in plain words:
   1. Download `statement-parser.skill`.
   2. In Claude, open Customize › Skills, remove the current "statement-parser" skill, then upload the file with "+" › Upload a skill.
   3. Open the library link, choose Share, and invite each bookkeeper in the firm with permission to edit (Contributor), so their new Parsers can be saved there. Only people in the same Claude organisation can save to it.
   4. Start a new chat to use the Firm Skill.

## The firm library

The library artifact's database holds one row per Firm Parser, so listing it never pulls in code:

- Collection `parsers`, document id = the Parser id (lowercase letters, digits and underscores, e.g. `anz_credit_card`). Fields: `statement_format`, `issuer`, `account_type` (`deposit` or `credit_card`), `signature` (list of issuer-level strings), `built` (YYYY-MM-DD), `promoted_in` (null, or the Firm Skill version that bundles it).
- Collection `parsers/<id>/files`, document `source`. Field: `code` (the Parser's Python source).
