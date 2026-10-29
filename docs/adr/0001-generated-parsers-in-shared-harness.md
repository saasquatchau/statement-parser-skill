# Parsers are generated code run by a shared harness

Each Statement Format gets its own generated parser script containing only the format-specific logic (Signature, Opening/Closing Balance, transaction rows). A shared harness, which is the same for every format, does text extraction, sign normalisation, Reconciliation, the Leak Scan, CSV writing and the pass/fail summary.

## Considered Options

- **Configuration files read by one shared engine** (column positions, date formats, header text). Rejected: real statements have quirks (multi-line descriptions, foreign-currency sub-rows, debits and credits in separate tables) that a configuration schema either can't express or grows into a bad programming language.
- **Fully generated scripts with no harness.** Rejected: each parser would carry its own copy of Reconciliation, so a generated parser could skip or weaken the check that defines success.

## Consequences

A parser cannot report success without Reconciliation, because the harness runs that check, not the parser. Don't "simplify" parsers into configuration files later without revisiting this.
