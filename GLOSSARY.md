# Statement Parser

Turns bank statement PDFs into reconciled transaction CSVs for bookkeepers, reusing a growing library of parsers so that routine runs never read statement content into the model's context.

## Language

### People

**Bookkeeper**:
The person running the skill, processing statements on behalf of clients.
_Avoid_: User, operator

**Client**:
The person or business whose statement is being processed; the owner of every account-identifying detail in it.
_Avoid_: Customer, account holder

**Firm**:
The bookkeeping practice a bookkeeper works for; the boundary inside which parsers built from its clients' statements may be shared.
_Avoid_: Organisation, tenant, practice

### Statements

**Statement**:
One PDF issued by a bank covering one period of one account, showing an opening balance, transactions and a closing balance; a PDF covering several accounts is not a Statement in v1.
_Avoid_: File, document, export

**Issuer**:
The bank or card provider that produced a statement.
_Avoid_: Bank (when the issuer is not strictly a bank), institution

**Account Type**:
Either credit card or deposit (checking/savings); determines the reconciliation direction.
_Avoid_: Product, account kind

**Scanned Statement**:
A statement with no text layer, read by OCR; it must still reconcile, and passes only with a warning to check the balances against the PDF.
_Avoid_: Image PDF, photo statement

**Opening Balance** / **Closing Balance**:
The balance printed for the start and end of the statement period, including its sign (CR/DR or minus).
_Avoid_: Available balance, amount due, credit limit (these are different fields)

**Money In**:
A transaction that increases the client's funds (or reduces what they owe on a credit card), recorded as a positive amount on every account type, as Xero expects.
_Avoid_: Debit, credit, Dr, Cr, deposit (debit and credit flip meaning between the bank's view and the client's books)

**Money Out**:
A transaction that reduces the client's funds (or increases what they owe on a credit card), recorded as a negative amount on every account type.
_Avoid_: Debit, credit, Dr, Cr, withdrawal, charge

### Parsing

**Statement Format**:
One distinct printed layout of statement, belonging to one issuer and one account type; an issuer may have several, e.g. after a redesign.
_Avoid_: Bank, template, layout version

**Parser**:
The reusable script that turns statements of exactly one Statement Format into transactions.
_Avoid_: Extractor, converter, bank script

**Signature**:
Issuer-level text that identifies a Statement Format without reading the statement into context.
_Avoid_: Fingerprint, matcher

**Reconciliation**:
The check that the opening balance plus the transactions equals the closing balance, in the direction set by the account type; a parse succeeds only if it reconciles.
_Avoid_: Validation, balancing

**Parser Library**:
Every Parser available to a firm: the Curated Parsers plus that firm's Firm Parsers.
_Avoid_: Registry, parser store, repository

**Leak Scan**:
The check that a new Parser contains none of the account-identifying details or transactions of the statement it was built from; a Build that fails it is rejected.
_Avoid_: Redaction, privacy check

**Bundled Parser**:
A Parser shipped inside the skill itself, so using it costs no tokens; either a Curated Parser or a Promoted Parser.
_Avoid_: Built-in, local parser

**Curated Parser**:
A Bundled Parser maintained by the skill's author in the public repository and supplied to every firm.
_Avoid_: Official parser, standard parser

**Firm Parser**:
A Parser built by one of a firm's bookkeepers and kept within that firm; it stays in the firm's library even after Promotion.
_Avoid_: Custom parser, local parser

**Promoted Parser**:
A Firm Parser that has been bundled into that firm's own copy of the skill; it never leaves the firm.
_Avoid_: Curated (Curated Parsers come from the skill's author, not a firm)

**Firm Skill**:
A firm's own copy of the skill, carrying the address of its library and its Promoted Parsers; every firm runs one from first use.
_Avoid_: Fork, custom skill, firm version

**Promotion**:
Rebuilding a firm's copy of the skill so that its Firm Parsers become Promoted Parsers, saving tokens on every Run that uses them.
_Avoid_: Publishing, upgrading, contributing (sharing parsers between firms is not Promotion)

**Build**:
Creating a new Parser from a statement whose Statement Format has none; the only step that reads statement content.
_Avoid_: Train, learn, onboard

**Run**:
Applying an existing Parser to a statement, producing either a reconciled CSV or a short failure report.
_Avoid_: Parse job, conversion

**Layout Drift**:
When a Parser that used to reconcile fails because the issuer changed its printed layout.
_Avoid_: Breakage, regression
