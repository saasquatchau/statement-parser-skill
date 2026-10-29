# 13: Build: a new Firm Parser from a statement

**What to build:** The only step that reads statement content, so it's the expensive one.

Spec stories: 26, 28–37.

**Blocked by:** 09: Leak Scan command; 11: Setup

**Status:** done

- [x] The skill asks before a Build, giving the estimated token cost
- [x] Layout Drift is reported with an offer to Build, never an automatic Build
- [x] The Build reads only the pages it needs
- [x] A new Parser is accepted only if it reconciles every statement of that Statement Format in the batch and passes the Leak Scan
- [x] After 3 failed attempts, the skill stops and reports what didn't add up
- [x] The Parser is saved to the firm library; if a matching Signature was saved in the meantime, that one is kept instead (first save wins)
- [x] A redesigned or scanned layout becomes a new Statement Format alongside the old one

## Comments

- 2026-10-29: Built. `harness pages` prints only the pages a Build needs (first and last by default). `harness check` accepts a candidate only if it follows the Parser contract, its Signature matches, it reconciles every matching statement in the batch, and it passes the Leak Scan; it counts attempts beside the candidate and says to stop after the third; with the library's Signatures it reports `EXISTS` so the first save wins; on acceptance it prints the library row. `BUILD.md` (read only during a Build) holds the Parser contract. SKILL.md has the Build steps: ask first with the token cost, read pages, write, check, save (create only, never overwrite), re-run. Manual check pending with `dist/demo-statement-new-bank.pdf`, a synthetic statement no Parser knows.
- 2026-10-29: Manual check passed in Claude chat with `dist/demo-statement-new-bank.pdf` (synthetic Kookaburra Credit Union). Claude listed the library (no match), asked before building with the token estimate, built `kookaburra_cu_transaction`, saved its row and code to the Bookkeeper Pty Ltd library, re-ran, and handed back a reconciled CSV. Pulled from the library and re-checked locally: Leak Scan passes, no member name, BSB or account digits in the source, direction inferred from the running balance, CSV correct. One `invalid_argument` (400) error from an artifact tool call early in the chat was recovered from automatically. Not yet seen in chat: a REJECT/retry cycle, the 3-attempt stop, EXISTS, and a save by a Contributor rather than the library owner.
