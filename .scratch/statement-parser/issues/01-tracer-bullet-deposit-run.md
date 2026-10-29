# 01: Tracer bullet: Run reconciles one deposit statement into a Xero CSV

**What to build:** The thinnest end-to-end Run. The harness CLI's `run` command takes an extracted-text fixture and a hand-written synthetic Parser for a made-up "Probe Bank" deposit account. It reconciles the statement, writes a Xero CSV and prints a one-line summary. Every later ticket adds behaviour to this same path. This ticket also sets up the test suite, which drives the CLI only (the one test seam in the spec).

The Parser contract set here (Signature, Opening/Closing Balance, transaction rows, Account Type) is the one every later Parser and every Build depends on (ADR-0001). Get it right, because changing it later means regenerating Parsers.

Spec stories: 1, 4–10, 27.

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `run` with a fixture and a Parser source writes one CSV with columns Date, Amount, Payee, Description, Reference
- [x] Dates are dd/mm/yyyy; Money In is positive and Money Out negative; Payee and Reference are blank; Description holds the printed transaction text
- [x] The stdout summary is one line per statement, and the exit code is 0 when the statement reconciles (deposit account: closing = opening + Σ amounts)
- [x] A fixture whose transactions don't add up fails with the check that failed and the size of the gap, writes no CSV, and exits non-zero
- [x] Neither the summary nor failure output contains any description text from the fixture
- [x] Tests drive the CLI and assert only on CSV contents, stdout and exit code
