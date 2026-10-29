# 15: First Curated Parsers with redacted fixtures

**What to build:** The first real formats: an ANZ credit card (debits and credits in separate tables) and one deposit account. This needs real statements from the skill's author and their sign-off on the redaction. Once the fixtures exist, an agent can write the Parsers and tests.

Spec stories: 17, 49, 50.

**Blocked by:** 03: Credit cards; 05: Dates from the statement period; 06: FX lines and split tables; 09: Leak Scan command

**Status:** done

- [x] Each Parser has a redacted fixture: extracted text with identities replaced and every amount kept, so it still reconciles
- [x] Each fixture passes the Leak Scan before it's committed
- [x] A fixture test for each Parser reconciles through `run`
- [x] The redaction is approved by the skill's author

## Comments

- 2026-10-29: Scope changed to the statements supplied: Amex Explorer (current layout, in credit), Amex Explorer (2020 layout, with foreign currencies), ANZ Business Essentials, ING Orange Everyday, Macquarie transaction account. First two Curated Parsers written: `amex_credit_card` and `amex_credit_card_2020`. Both reconcile their real statements, pass the Leak Scan, and contain no personal details. The 2026 Parser doesn't match the 2020 layout (BUILD, not a wrong match), confirming they're separate Statement Formats. `scripts/redact.py` produces redacted text fixtures (tested); redacted Amex fixtures are in `private/redacted/` awaiting the author's review before they move to `tests/fixtures/curated/`. Finding: Amex lists charges dated a day or two before the statement period, so every Amex statement triggers the out-of-period warning. ANZ, ING and Macquarie are still to do.
- 2026-10-29: Amex fixtures reviewed and committed to tests/fixtures/curated/ with tests. Redaction now also replaces Australian localities (from Australia Post's postcode booklet via scripts/localities.py, kept in private/) and postcodes, protecting month names and Parser labels, plus `--also` terms named by the reviewer. Three more Curated Parsers written and accepted against the real statements: `anz_business_essentials` (only 1 transaction in the sample: needs a busier statement), `ing_orange_everyday`, `macquarie_savings`. Running all five statements together found ANZ's account number being misread (interleaved page-1 columns); fixed, and the harness now fails any statement whose account number has fewer than 4 digits rather than merging accounts. Redacted fixtures for the three are in private/redacted/ awaiting review. OCR verified in chat (ticket 08).
- 2026-10-29: ANZ, ING and Macquarie fixtures reviewed (ING account nickname removed with `--also`) and added with tests; every Curated Parser now has a fixture, enforced by a test. Out-of-period warnings now fire only for dates more than 31 days outside the period, so Amex's charges from just before the cut-off no longer warn. Follow-up: a busier ANZ Business Essentials statement to prove that Parser beyond its single transaction.
