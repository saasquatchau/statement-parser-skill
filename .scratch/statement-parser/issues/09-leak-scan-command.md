# 09: Leak Scan command

**What to build:** Builds, Promotion and Curated fixtures all depend on this, so it comes early, as a second command on the same harness CLI.

Spec stories: 33, 34, 50.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] `leak-scan` collects the account-identifying values from a statement input (account numbers, BSB, holder name, address lines)
- [x] It fails if any of those values appears in the Parser source
- [x] A failure says which kind of value leaked, never the value itself
- [x] A Parser using only issuer-level text passes
