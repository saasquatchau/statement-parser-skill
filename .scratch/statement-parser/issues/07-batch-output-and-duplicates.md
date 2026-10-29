# 07: Batch output: combined CSVs and the duplicate-row warning

**What to build:** How a batch of statements becomes files the bookkeeper imports into Xero, plus the final script that flags possible duplicates.

Spec stories: 19–22.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] By default, `run` writes one CSV per account per batch (account = issuer, Account Type and last 4 digits), rows in date order
- [x] The per-statement option writes one CSV per statement
- [x] Failed statements are left out of the CSV and listed in the summary
- [x] File names show bank, Account Type, last 4 digits and period
- [x] Identical (date, amount, description) rows are flagged on stdout by row number, date and amount only, never description, with at most 5 listed
- [x] Nothing is removed from the CSV by the duplicate check
