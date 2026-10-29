"""Builds a list of Australian locality names from Australia Post's postcode booklet (the free PDF from
auspost.com.au/postcode), for scripts/redact.py.

    python scripts/localities.py <postcode booklet.pdf> <out.txt>

The list stays in private/: it's derived from Australia Post's data, so it isn't committed.
"""
import re
import sys

import pdfplumber

STATES = "NSW|VIC|QLD|SA|WA|TAS|NT|ACT"
ENTRY = re.compile(rf"^([A-Z][A-Z'’ .-]*?) ({STATES}) \d{{4}}$")
STATE_ONLY = re.compile(rf"^({STATES}) \d{{4}}$")
UPPER = re.compile(r"^[A-Z][A-Z'’ .-]*$")
COLUMN_STARTS = [28, 143, 253, 368, 478, 593, 703]


def column_lines(page):
    edges = COLUMN_STARTS + [page.width]
    for left, right in zip(edges, edges[1:]):
        text = page.crop((left - 2, 0, right - 2, page.height)).extract_text() or ""
        yield from (line.strip() for line in text.splitlines())


def localities(pdf_path):
    names = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pending = ""  # a long name wrapped onto the next line, before its state and postcode
            for line in column_lines(page):
                if m := ENTRY.match(line):
                    names.add(f"{pending} {m[1]}".strip() if pending else m[1])
                    pending = ""
                elif STATE_ONLY.match(line) and pending:
                    names.add(pending)
                    pending = ""
                elif UPPER.match(line) and len(line) > 1:
                    pending = f"{pending} {line}".strip()
                else:
                    pending = ""
    return sorted(names)


if __name__ == "__main__":
    found = localities(sys.argv[1])
    with open(sys.argv[2], "w") as f:
        f.write("\n".join(found) + "\n")
    print(f"{len(found)} localities")
