# 02: PDF statements as input

**What to build:** Real statements are PDFs, while fixtures are text, so this adds the PDF path into the same entry point. Tests generate synthetic PDFs the way the Cowork probe built its single-page statement, so no real statement is needed.

Keep the harness's extracted-text output stable, because Parsers are written against it.

Spec stories: 1, 23.

**Blocked by:** 01: Tracer bullet

**Status:** done

- [x] `run` accepts a PDF and produces the same CSV and summary as the matching text fixture
- [x] Extraction works under Python 3.10 with pdfplumber, with nothing installed at run time
- [x] Tests use synthetic PDFs generated within the test suite
