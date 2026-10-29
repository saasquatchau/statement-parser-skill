# 06: FX lines and split debit/credit tables

**What to build:** Two row rules that mostly serve particular banks: foreign-currency detail lines (Amex-style) and statements that print debits and credits in separate tables (ANZ credit cards).

Spec stories: 11, 12, 17, 18.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] A foreign-currency transaction is recorded at its AUD amount
- [x] The bank's full conversion text is appended verbatim to Description
- [x] FX detail lines never become rows of their own
- [x] Separate debit and credit tables are merged into date order, keeping the printed order within a date
