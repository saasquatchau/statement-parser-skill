# Runs happen in the cloud sandbox; Firm Parsers live in an artifact database

Statements are attached in chat and exist only in Claude's cloud sandbox (`/mnt/user-data/uploads`, read-only, never loaded into context unless opened). So Runs happen there: the harness and Curated Parsers are bundled in the skill and run in place, and Firm Parsers are kept in a per-firm artifact database (the pattern the dumpling-sauce skill uses) and written into the sandbox only when needed. This supersedes ADR-0002.

## Considered Options

- **Cowork with a Parser Library folder (ADR-0002).** Probing showed Cowork has two separate sandboxes: the cloud one holds attachments and skill files; the one on the user's computer holds connected folders. Parsers in the folder can't reach attached statements without the model carrying the PDF across, which breaks the sealed-statement rule.
- **Statements dropped into a connected folder instead of attached.** Zero-token Runs, but abandons chat as the bookkeeper's interface, and firm-wide sharing would rely on an untested synced folder.

## Consequences

- A Run with a Curated Parser costs a command plus a summary. A Run with a Firm Parser additionally costs carrying that parser's code into the sandbox (~2–3k tokens, once per Statement Format per conversation).
- Works in ordinary Claude chat as well as Cowork; no folder to connect.
- Firm-wide sharing relies on artifact write access, which only members of the artifact owner's organisation have.
- Statements are sealed: the model passes their paths to the harness and never opens them, except during a Build.
