# Every firm runs its own copy of the skill from day one

The published skill is identical for every firm, so it can't carry a firm's library address. On first use the skill creates the firm's library artifact and rebuilds itself into a Firm Skill with that address written in, then walks the bookkeeper through uploading it. First-time setup and Promotion are therefore the same flow, and a firm upgrades by installing a new Curated release and Promoting again (its Firm Parsers survive in the library, so nothing is lost in between).

## Considered Options

- **Find the library by listing the bookkeeper's artifacts each conversation.** Unverified in chat and costs tokens on every Run.
- **Ask the bookkeeper for the library URL each conversation.** Tedious, and error-prone.
