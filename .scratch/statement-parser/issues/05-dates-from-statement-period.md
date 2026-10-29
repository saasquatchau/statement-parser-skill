# 05: Dates from the statement period

**What to build:** Many statements print dates without a year. The harness works out the year from the printed statement period, once for every Parser, so no Parser gets it wrong on its own.

Spec stories: 13, 14.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] A statement whose period runs from December to January dates its January rows in the following year
- [x] Year inference uses the statement period, never today's date
- [x] A transaction date outside the statement period is flagged in the summary
