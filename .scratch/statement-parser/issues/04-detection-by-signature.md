# 04: Detection by Signature across Bundled and Firm Parsers

**What to build:** The harness chooses the Parser itself. Parser sources are passed in order of precedence, Bundled first, so the lookup order (Bundled Parsers before Firm Parsers) lives in the harness, not in the skill's instructions.

Spec stories: 2, 3, 41.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] A single Signature match uses that Parser
- [x] No match is reported in the summary as a Build candidate
- [x] Ambiguous matches name the candidate Statement Formats, so the skill can ask the bookkeeper
- [x] When a Bundled and a Firm Parser both match, the Bundled one is tried first, and the Firm one only if the Bundled one fails to reconcile
- [x] Detection output never includes statement text
