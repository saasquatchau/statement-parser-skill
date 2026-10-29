# 14: Promotion and re-Promotion after an upgrade

**What to build:** Turns Firm Parsers into Promoted Parsers in the firm's own Firm Skill, and recovers cleanly after the firm installs a new Curated release (ADR-0004).

Spec stories: 43–48, 51.

**Blocked by:** 09: Leak Scan command; 12: Runs with Firm Parsers

**Status:** done

- [x] Promotion runs only when a bookkeeper asks for it
- [x] It rebuilds the Firm Skill from the installed skill's files plus the Firm Parsers, each re-checked by the Leak Scan
- [x] It marks the promoted rows in the library with the version, and hands back the zip with upload instructions
- [x] Firm Parsers stay in the library after Promotion
- [x] After a new Curated release is installed, rows marked promoted but not bundled fall back to the library, and the skill suggests Promoting again

## Comments

- 2026-10-29: Built. `harness firm-skill --promote <folder>` rebuilds the installed Firm Skill with the folder's Firm Parsers under `parsers/promoted/` (keeping ones already promoted), bumps `version` in firm.json (Setup is v1), and prints which ids to mark `promoted_in` with which version. With no statement to check against, Promotion's Leak Scan rejects any Parser containing a run of 6+ digits; the full Leak Scan ran at Build time. Runs include `parsers/promoted`; `detect` never fetches a Parser the skill already bundles, so after a fresh Curated install the library rows are fetched again and the existing TIP suggests Promoting. SKILL.md has the Promotion steps. Manual check pending.
- 2026-10-29: Manual check passed in Claude chat. "promote our parsers" fetched the two unbundled Firm Parsers, built Firm Skill v2 with 3 Bundled Parsers, and set `promoted_in: "v2"` on both library rows (confirmed by reading the library). After installing v2, the Kookaburra demo statement passed with no library fetch and no TIP. Found: the skill only triggered when invoked as `/statement-parser`, because its description didn't mention Setup, Builds or Promotion; description widened. The re-Promotion-after-Curated-reinstall path is covered by tests but not yet seen in chat.
