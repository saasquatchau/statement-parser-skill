# Spec: Statement Parser skill (v1)

Status: ready-for-agent

## Problem Statement

Bookkeepers receive bank statements from their clients as PDFs and need the transactions in Xero. Copying them by hand is slow and error-prone. Asking Claude to read each PDF works, but it is expensive: every statement is 10–30k tokens of context, every month, for every client. And nothing proves the numbers are right. A misread amount or a missed row goes into the books silently.

Bookkeepers want to drop statements into Claude chat and get back a Xero-ready CSV they can trust, cheaply, without managing scripts, folders or configuration.

## Solution

A Claude skill that turns bank statement PDFs into Xero CSVs that reconcile, using a growing library of Parsers so that routine Runs never read statement content into context.

- The bookkeeper attaches statements in Claude chat. Statements are **sealed**: the model passes their file paths to a script and never opens them, except during a Build.
- A shared harness, bundled in the skill, picks the Parser for each statement by **Signature**, runs it, checks **Reconciliation** (opening balance + transactions = closing balance), and writes the CSV. The bookkeeper sees a short summary: which statements passed, which failed and why, and any warnings.
- A statement passes only if it reconciles. A script that runs but produces wrong numbers is a failure.
- When no Parser exists for a **Statement Format**, the skill offers a **Build**, saying how many tokens it will cost. In a Build, Claude reads the statement once, writes a new Parser, and keeps it only if it reconciles and passes the **Leak Scan**. The new Parser is saved as a **Firm Parser** in the firm's library, so every bookkeeper in the firm can reuse it.
- **Bundled Parsers** (Curated Parsers from the author's public repository, plus the firm's Promoted Parsers) ship inside the skill and cost no tokens to use. Firm Parsers cost a little each conversation. When a Run uses Firm Parsers, the skill suggests **Promotion**: it rebuilds the firm's own copy of the skill (the **Firm Skill**) with them bundled, and gives step-by-step upload instructions.
- Every firm runs its own Firm Skill from first use. Setup creates the firm's library and produces the Firm Skill through the same flow as Promotion.

## User Stories

### Running statements

1. As a bookkeeper, I want to attach one or more statement PDFs in Claude chat and ask for Xero CSVs, so that I don't have to type transactions by hand.
2. As a bookkeeper, I want the skill to recognise which bank and account type each statement is from without me saying, so that I can drop in a mixed pile of statements.
3. As a bookkeeper, I want to be asked when the skill can't tell which Parser fits, so that it never guesses silently.
4. As a bookkeeper, I want every statement checked so that opening balance plus transactions equals closing balance, so that I can trust the CSV without re-checking every line.
5. As a bookkeeper, I want a statement that doesn't reconcile to be reported as a failure and left out of the CSV, so that wrong numbers never reach Xero.
6. As a bookkeeper, I want failure messages to say which check failed (for example, "closing balance off by 12.40"), so that I know what to look at.
7. As a firm owner, I want failure messages and summaries to contain no statement content, so that client data doesn't spread through chat history unnecessarily.
8. As a bookkeeper, I want the CSV to use Xero's sign convention (Money In positive, Money Out negative) on every account type, so that I can import it without editing.
9. As a bookkeeper, I want the CSV in Xero's bank statement layout (Date, Amount, Payee, Description, Reference) with dates as dd/mm/yyyy, so that it imports into an Australian Xero organisation first time.
10. As a bookkeeper, I want the full printed transaction text in Description, so that Xero bank rules can match on it.
11. As a bookkeeper, I want foreign-currency transactions recorded at their AUD amount, with the bank's full conversion text appended to Description (as Amex prints it), so that the CSV reconciles and I can still see the original currency.
12. As a bookkeeper, I want the extra FX detail lines on a statement never to become rows of their own, so that the CSV has no phantom transactions.
13. As a bookkeeper, I want transactions in a statement that spans December to January to get the right year, so that dates are never a year out.
14. As a bookkeeper, I want a transaction dated outside the statement period to be flagged, so that I notice a date problem before importing.
15. As a bookkeeper, I want a credit card's opening and closing balances read correctly even when the card is in credit (an overpaid card), so that reconciliation works in every case.
16. As a bookkeeper, I want an overdrawn deposit account's balances read correctly (CR/DR suffix or minus sign), so that reconciliation works in every case.
17. As a bookkeeper, I want ANZ credit card statements, which print debits and credits in separate tables, merged into one date-ordered list, so that the CSV reads like the account history.
18. As a bookkeeper, I want transactions sorted by date, keeping the printed order within each date, so that the CSV is predictable.
19. As a bookkeeper, I want one combined CSV per account for a batch by default, so that I import a year of statements for an account in one go.
20. As a bookkeeper, I want the option of one CSV per statement, so that I can import a single month or fix a single statement.
21. As a bookkeeper, I want CSV file names that show the bank, account type, the last 4 digits of the account and the period, so that I import each file into the right Xero bank account.
22. As a bookkeeper, I want possible duplicate rows in a CSV flagged in the summary by row number, date and amount, so that I catch a statement dropped in twice without legitimate identical purchases being deleted.
23. As a bookkeeper, I want the CSVs handed back as downloads in chat, so that I never deal with folders.
24. As a bookkeeper, I want a statement with no text layer (a scan) read by OCR and still required to reconcile, with a warning to check the balances against the PDF, so that scanned statements are usable but treated with suspicion.
25. As a bookkeeper, I want a statement covering several accounts rejected with a clear "not supported" message, so that I know to split it or handle it by hand.
26. As a bookkeeper, I want a statement whose Parser used to work, but now fails, reported as possible Layout Drift with an offer to Build, so that I decide whether to spend tokens.
27. As a bookkeeper, I want a batch to be one turn with one short line per statement, so that processing a year of statements costs almost nothing.

### Building parsers

28. As a bookkeeper, I want to be told when there's no Parser for a statement and asked before a Build, with the estimated token cost, so that expensive steps never happen by surprise.
29. As a bookkeeper, I want a Build to read only the pages needed to understand the layout, so that it costs as little as possible.
30. As a bookkeeper, I want a new Parser accepted only if it reconciles every statement of that Statement Format in the batch, so that a Parser that fits one statement by luck isn't kept.
31. As a bookkeeper, I want a Build to stop after 3 failed attempts and report what didn't add up, so that a hard statement can't burn unlimited tokens.
32. As a bookkeeper, I want a Build that picked the wrong balance field (available balance, credit limit, minimum payment, amount due) to fail Reconciliation straight away, so that mistakes surface at Build time, not after import.
33. As a firm owner, I want every new Parser checked by the Leak Scan, so that no client's account number, BSB, name or address ends up in parser code that other bookkeepers will run.
34. As a firm owner, I want Signatures and layout anchors limited to issuer-level text (bank name, printed headings, column titles), so that Parsers are about formats, not clients.
35. As a bookkeeper, I want a Parser I build to be available straight away to everyone in my firm, so that colleagues don't pay for the same Build.
36. As a bookkeeper, I want two colleagues building the same Statement Format at once to end up with one Parser, the first saved, so that the library has no duplicates or clashes.
37. As a bookkeeper, I want a bank's redesigned statement to become a new Statement Format alongside the old one, so that older statements still parse.
38. As a bookkeeper, I want a scanned version of a known format to be treated as its own Statement Format, so that OCR quirks don't break the Parser for the digital version.

### Library, Setup and Promotion

39. As a firm owner setting up for the first time, I want the skill to create my firm's library and hand me my Firm Skill with upload instructions, so that setup is one guided step.
40. As a firm owner, I want instructions for sharing the library with my bookkeepers, so that they can save Firm Parsers too.
41. As a bookkeeper, I want Bundled Parsers tried first, and the firm's library consulted only when none match or reconcile, so that common banks cost no tokens.
42. As a bookkeeper, I want the skill to suggest Promotion when a Run had to load Firm Parsers, at most once per conversation, so that I know how to cut future costs.
43. As a firm owner, I want Promotion to run only when someone asks for it, so that the skill never changes itself unasked.
44. As a firm owner, I want Promotion to re-run the Leak Scan on every Firm Parser it bundles, so that nothing unsafe is bundled.
45. As a firm owner, I want Promotion to produce a downloadable Firm Skill and plain upload instructions, so that a non-technical person can install it.
46. As a firm owner, I want Firm Parsers to stay in the library after Promotion, so that installing a new Curated release never loses them.
47. As a firm owner, I want the skill to notice Firm Parsers marked promoted that the installed skill doesn't bundle, and suggest Promoting again, so that upgrading to a new Curated release is one step.
48. As a firm owner, I want Promoted Parsers never to leave my firm, so that parsers built from my clients' statements stay with us.

### Maintaining Curated Parsers

49. As the skill's author, I want each Curated Parser to ship with a redacted fixture (extracted text with identities replaced and amounts kept), so that I can re-test every Curated Parser when the harness changes.
50. As the skill's author, I want fixtures to pass the Leak Scan before they're committed, so that the public repository never contains client data.
51. As the skill's author, I want to release new Curated Parsers and harness versions by publishing the skill, so that firms upgrade by installing it and Promoting.

## Implementation Decisions

- **Runtime** (ADR-0003): everything runs in Claude's cloud sandbox, where attached statements live (read-only). The harness and Bundled Parsers run in place from the skill's own files. Cowork's local sandbox is not used (ADR-0002 is superseded).
- **Sealed statements:** outside a Build, the model only ever passes statement file paths to the harness. It never opens, extracts or prints statement content itself.
- **Parser shape** (ADR-0001): one generated Python Parser per Statement Format, holding only format-specific logic: its Signature, where the Opening and Closing Balances are, how to read transaction rows, and its Account Type. Everything shared lives in the harness: text extraction, OCR, detection, year inference from the statement period, sign normalisation, Reconciliation, the Leak Scan, CSV writing, the duplicate-row check and the summary.
- **Python 3.10 baseline,** with pdfplumber, pypdf, pypdfium2, pdfminer, pytesseract and the tesseract binary available (confirmed by the probe on 2026-10-29). PyMuPDF and ocrmypdf are not available. The harness must not depend on installing packages at run time.
- **Harness CLI is the one test seam:**
  - The `run` command takes statement inputs and one or more Parser sources. It writes CSVs to an output location, prints the Run summary to stdout, and exits 0 only if every statement reconciled.
  - A statement input may be a PDF or an extracted-text fixture. Fixtures skip extraction and OCR.
  - A per-statement option switches off combining.
  - The `leak-scan` command takes a Parser and a statement input and reports pass/fail without printing the leaked values.
- **Detection order** (Q26): Bundled Parsers first. Firm Parsers' Signatures are loaded from the firm library only when no Bundled Parser matches and reconciles. More than one match is reported as ambiguous, for the skill to ask the bookkeeper. No match means a Build candidate.
- **Sign convention:** Money In positive, Money Out negative, on every Account Type, matching Xero. The terms debit, credit, Dr and Cr are not used. Reconciliation:
  - deposit account: closing = opening + Σ amounts
  - credit card (balance owed printed positive): closing = opening − Σ amounts
  - Balance signs come from the printed CR/DR suffix or minus sign.
- **Multi-account detection:** more than one Opening/Closing Balance pair rejects the statement as unsupported.
- **Scanned Statements:** a statement with no text layer goes through tesseract OCR. It must still reconcile, and its summary line carries a "check balances against the PDF" warning. Scanned and digital copies of one layout are separate Statement Formats.
- **Year inference:** dates without a year take it from the printed statement period. Dates outside the period are flagged.
- **FX lines:** the AUD amount is the transaction amount. The bank's conversion text is appended verbatim to Description. Detail lines never become rows.
- **Xero CSV:** the columns are Date, Amount, Payee, Description and Reference. Dates are dd/mm/yyyy. Payee and Reference are blank. Rows are in date order, keeping the printed order within a date.
- **Combining:** by default one CSV per account per batch (account identified by issuer, Account Type and last 4 digits), or one per statement on request. Failed statements are left out and listed. The file name shows bank, Account Type, last 4 digits and period.
- **Duplicate-row check:** a final script over each output CSV flags identical (date, amount, description) rows as a warning in stdout. Rows are identified by row number, date and amount, never description, with at most 5 listed. Nothing is removed.
- **Summary format:** one short line per statement (pass, fail with the check that failed, or warning), plus batch-level warnings and at most one Promotion suggestion. No statement content.
- **Build flow:**
  1. Confirm with the bookkeeper, giving the estimated token cost.
  2. Read the extracted text of only the needed pages.
  3. Write the Parser.
  4. Accept it only if it reconciles every statement of that format in the batch and passes the Leak Scan, within at most 3 attempts.
  5. Save it to the firm library. If a Parser with a matching Signature was saved in the meantime, keep that one instead (first save wins).
- **Leak Scan:** the account-identifying values (account numbers, BSB, holder name, address lines) are collected from the statement being built from. The Build fails if any of them appears in the Parser source. Only issuer-level text is allowed in Signatures and anchors.
- **Firm library** (ADR-0003, ADR-0004): an artifact database owned by someone in the firm's organisation, shared with its bookkeepers as Contributors. Each Firm Parser record holds the Parser source, its Signature, its Statement Format name, Account Type, build date and a promoted-in-version marker. Records are never deleted by Promotion.
- **Firm Skill, Setup and Promotion** (ADR-0004): the published Curated skill can't carry a firm's library address.
  - On first use, Setup creates the firm library and rebuilds the skill into a Firm Skill with that address, then gives upload and sharing instructions.
  - Promotion rebuilds the Firm Skill from the installed skill's own files, adds the Firm Parsers (re-checked by the Leak Scan) and marks their library records as promoted in that version.
  - Rows marked promoted but missing from the installed skill fall back to library loading, and the skill suggests Promotion.
- **Curated Parsers** live in the author's public repository with redacted fixtures, and are bundled into the published skill.

## Testing Decisions

- **Good tests** drive the harness CLI with statement inputs and assert only on its external behaviour: which CSV files exist and their exact contents, the stdout summary lines, and the exit code. They don't test parser internals or harness helper functions directly.
- **One seam:** the harness CLI, with its `run` and `leak-scan` commands. Extracted-text fixtures go through the same entry point as PDFs.
- **Inputs:**
  - Redacted text fixtures, which are the Curated Parser fixtures.
  - Synthetic PDFs generated in the test suite, the same way the Cowork probe built its single-page statement, covering the PDF path.
  - Rendered-image PDFs of those synthetic statements, covering OCR.
- **Behaviours to cover:**
  - Detection: a single match, ambiguous matches, no match, and Bundled Parsers taking precedence over Firm Parsers.
  - Reconciliation pass and fail, on both deposit and credit card accounts.
  - Balances crossing zero, with CR/DR suffixes and minus signs.
  - A wrong balance field caught at Build time.
  - Year inference across December–January, and flagging dates outside the period.
  - FX prose appended, with no phantom rows.
  - Merging tables split by debit and credit.
  - Combined versus per-statement CSVs, and failed statements left out.
  - The duplicate-row warning: no descriptions in the output, at most 5 listed.
  - Multi-account rejection, and the Scanned Statement warning.
  - Summaries and failures never containing fixture descriptions or identities.
  - Leak Scan pass and fail.
- **Every Curated Parser** has at least one fixture test that reconciles.
- **Prior art:** none in the repository yet. The Cowork probe's synthetic-PDF builder is the pattern for generated PDFs.
- **Manual scenario checks,** not automated, because they depend on the model and the Claude app. Run each in a real Claude chat:
  - Setup end to end: the library is created and the Firm Skill zip is handed back with instructions.
  - A Run with a Bundled Parser: confirm the statement is never opened.
  - A Run with a Firm Parser: the Promotion suggestion appears.
  - A Build: confirmation with the cost, the 3-attempt cap and the Leak Scan rejection.
  - A Promotion and re-upload.
  - Installing a new Curated release, then the re-Promotion suggestion.
  - Two bookkeepers building the same format.

## Out of Scope

- Statements covering more than one account.
- CSV or other non-PDF bank exports.
- Continuity checks between consecutive statements.
- Removing duplicates automatically, and checking for overlapping statement periods.
- Sharing parsers between firms, such as pull requests from firms to the Curated repository (v2).
- Import layouts for anything other than Xero (MYOB, QuickBooks and others).
- Running in Cowork's local sandbox or Claude Code as a supported target.
- Splitting Payee from Description.

## Further Notes

- Not yet verified, and the first things to check when building starts: creating the library artifact from inside chat, and handing back a rebuilt skill as a downloadable zip. The dumpling-sauce skill suggests artifact database reads and writes from chat work.
- The cloud sandbox reaches the network only through an allow-list proxy, and org owners can turn network access off. The harness must not depend on network access.
- Token budget, for reference: a Run with a Bundled Parser costs a command plus a summary. A Firm Parser adds about 2–3k tokens once per Statement Format per conversation. A Build costs about 20–40k tokens.
- See GLOSSARY.md for terms and ADRs 0001, 0003 and 0004 for the decisions behind this spec.
