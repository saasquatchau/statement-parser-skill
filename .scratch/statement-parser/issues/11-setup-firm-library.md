# 11: Setup: firm library and Firm Skill hand-back

**What to build:** Proves the two platform features the spec lists as unverified. If either one fails, revisit ADR-0003 or ADR-0004 before tickets 12–14.

Spec stories: 39, 40.

**Blocked by:** 10: Skill v0

**Status:** done

- [x] On first use, the skill creates the firm library artifact (database capability) from inside chat
- [x] It rebuilds itself into a Firm Skill zip with the library's address written in, and hands it back as a download
- [x] It gives plain upload instructions
- [x] It gives instructions for sharing the library with the firm's bookkeepers as Contributors

## Comments

- 2026-10-29: Built `harness firm-skill` (tested), the bundled library page, and the Setup section of SKILL.md. Manual check in Claude chat: Setup for "Bookkeeper Pty Ltd" published the library artifact with the `db` capability declared, and `firm-skill` handed back `statement-parser.zip` with upload and sharing steps. The library's `parsers` collection is readable (empty) as the owner and at Contributor (`interact`) level. Still to confirm: that removing the old skill and uploading the Firm Skill works as the steps say. Contributors' write access is checked in ticket 13, when the first Firm Parser is saved.
- 2026-10-29: Replacing the skill confirmed: after removing the old skill and uploading the Firm Skill, a new chat recognised the firm as already set up (it read firm.json) and ran a real statement, correctly reporting BUILD.
