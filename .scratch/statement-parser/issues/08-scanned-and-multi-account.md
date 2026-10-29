# 08: Scanned Statements and multi-account rejection

**What to build:** OCR for statements with no text layer, and a clear rejection for statements covering more than one account.

Spec stories: 24, 25, 38.

**Blocked by:** 02: PDF statements as input

**Status:** done

- [x] A PDF with no text layer goes through tesseract OCR
- [x] A Scanned Statement must still reconcile, and its summary line carries a "check balances against the PDF" warning
- [x] A statement with more than one Opening/Closing Balance pair is rejected as unsupported
- [x] Tested with synthetic PDFs rendered to images

## Comments

- 2026-10-29: Implemented. The OCR test is skipped locally because the tesseract binary isn't installed on the dev machine, so the two OCR criteria are unverified. Install tesseract (`brew install tesseract`) and run the suite to confirm, then mark this done.
- 2026-10-29: OCR verified in Claude chat with `dist/demo-statement-scanned.pdf` (image only, no text layer): tesseract in the sandbox read it, it reconciled, and the summary carried the "check balances against the PDF" warning.
