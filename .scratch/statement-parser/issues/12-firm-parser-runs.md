# 12: Runs with Firm Parsers and the Promotion suggestion

**What to build:** When no Bundled Parser fits, the skill falls back to the firm library, carrying only the matching Parser into the sandbox.

Spec stories: 35, 41, 42.

**Blocked by:** 11: Setup

**Status:** done

- [x] When no Bundled Parser matches and reconciles, the skill loads Firm Parser Signatures from the library
- [x] Only the matching Firm Parser is carried into the sandbox and Run
- [x] The summary suggests Promotion at most once per conversation, only when a Firm Parser was loaded
- [x] Tested with a Firm Parser seeded into the library by hand, so this doesn't wait for Builds

## Comments

- 2026-10-29: Built. `harness detect` matches library Signatures against sealed statements and prints which Firm Parsers to fetch; `run --firm-parsers` tries them after Bundled Parsers and ends with a `TIP` line suggesting Promotion. SKILL.md has the fallback steps and the library layout (`parsers` rows hold metadata and Signature; code is in `parsers/<id>/files/source`). Criteria to tick after the manual check with a Firm Parser seeded into the real library.
- 2026-10-29: First manual check skipped the library: the bundled Parser's `FAIL` was reported straight away. Fixed by having Firm Skill runs print a `NEXT` line naming the library whenever a statement didn't reconcile, and making SKILL.md's fallback follow that line.
- 2026-10-29: Manual check passed with the test Parser `probe_bank_deposit_2027` seeded into the Bookkeeper Pty Ltd library: bundled Parser failed, `NEXT` led to the library, only that Parser was fetched, the re-run passed with the CSV, and the `TIP` was relayed. The seeded test row stays in the library for ticket 14's Promotion check.
