"""Turns a real statement into a redacted text fixture for tests/test_private_fixtures.py (write it to
private/fixtures/curated/<parser id>.txt; it is never committed, even redacted).

    python scripts/redact.py <statement> <parser.py> <out.txt> [--localities private/localities.txt]
                             [--names private/first_names.txt] [--also TERM ...]

Replaces what the Parser reads as identifiers (holder name, account number, BSB, address), email addresses,
long reference numbers, Australian locality names (from scripts/localities.py; private/localities.txt by default),
first names (from scripts/names.py; private/first_names.txt by default) and postcodes, keeping every amount, so the
fixture still reconciles. Month names and any word the Parser itself matches on are never treated as a locality or
a name. --also redacts extra terms the reviewer spots (other people's names,
places glued to other words). Always review the output by eye
before relying on it: descriptions are kept, and only you can judge whether they say too much.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.cli import apply  # noqa: E402
from harness.extract import statement_text  # noqa: E402
from harness.parsers import load_parser  # noqa: E402

PLACEHOLDER_ADDRESS = ["1 SAMPLE STREET", "SAMPLEVILLE VIC 3000"]
LONG_NUMBER = re.compile(r"(?<![\d.,])\d{8,}(?![\d.,])")
STATES = {"NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"}
POSTCODE = re.compile(rf"\b({'|'.join(STATES)}) \d{{4}}\b")
MONTHS = {"JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER",
          "NOVEMBER", "DECEMBER", "JAN", "FEB", "MAR", "APR", "JUN", "JUL", "AUG", "SEP", "SEPT", "OCT", "NOV", "DEC"}
DEFAULT_LOCALITIES = ROOT / "private" / "localities.txt"
DEFAULT_NAMES = ROOT / "private" / "first_names.txt"


def word_list_pattern(path, parser_source):
    """One case-insensitive pattern for every entry in a word list (localities or names), longest first, leaving out
    months and anything the Parser matches on (its string literals), so redaction never breaks the layout the
    Parser reads."""
    protected = MONTHS | STATES | {w.upper() for literal in re.findall(r'"([^"]*)"', parser_source)
                          for w in re.findall(r"[A-Za-z]+", literal)}
    names = [n for n in Path(path).read_text().splitlines() if n and n.upper() not in protected]
    names.sort(key=len, reverse=True)
    # Not inside web or email addresses: "com" in "amex.com.au" isn't a name.
    return re.compile(r"(?<![A-Za-z./@])(?:" + "|".join(map(re.escape, names)) + r")(?![A-Za-z]|\.[A-Za-z])",
                      re.IGNORECASE)


def zeros(match):
    return re.sub(r"\d", "0", match.group(0))


def redact(text, identifiers, localities=None, names=None, also=()):
    replacements = [(term, "REDACTED") for term in also]
    name = identifiers.get("holder_name")
    if name:
        replacements.append((name, "PAT SAMPLE"))
        replacements += [(word, "SAMPLE") for word in name.split() if len(word) >= 3]
    for line, placeholder in zip(identifiers.get("address") or [], PLACEHOLDER_ADDRESS * 2):
        replacements.append((line, placeholder))
    for key in ("account_number", "bsb"):
        value = identifiers.get(key)
        if value:
            replacements.append((value, re.sub(r"\d", "0", value)))
            digits = re.sub(r"\D", "", value)
            if len(digits) >= 5:
                # Masked or reformatted copies elsewhere (e.g. "XXXXXXXXXX11001") share the trailing digits.
                replacements.append((digits[-5:], "00000"))
    for old, new in sorted(replacements, key=lambda r: -len(r[0])):
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "redacted@example.com", text)
    text = POSTCODE.sub(lambda m: f"{m[1]} 0000", text)
    if localities:
        text = localities.sub("SUBURB", text)
    if names:
        text = names.sub("NAME", text)
    return LONG_NUMBER.sub(zeros, text)


def word_list(path, default, parser_source):
    path = path or (default if default.exists() else None)
    return word_list_pattern(path, parser_source) if path else None


def main(statement, parser_path, out, localities_path=None, names_path=None, also=()):
    parser = load_parser(parser_path)
    parser_source = Path(parser_path).read_text()
    text = statement_text(statement)[0]
    localities = word_list(localities_path, DEFAULT_LOCALITIES, parser_source)
    names = word_list(names_path, DEFAULT_NAMES, parser_source)
    redacted = redact(text, parser.parse(text)["identifiers"], localities, names, also)
    result, reason = apply(parser, redacted)
    if result is None:
        print(f"FAIL  redacted text no longer parses: {reason}")
        return 1
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(redacted)
    print(f"OK    {Path(out).name}: {len(result['transactions'])} transactions, reconciles. Review it; keep it in private/.")
    return 0


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("statement")
    cli.add_argument("parser")
    cli.add_argument("out")
    cli.add_argument("--localities", help="Locality list from scripts/localities.py")
    cli.add_argument("--names", help="First-name list from scripts/names.py")
    cli.add_argument("--also", action="append", default=[], help="Another term to redact; repeat as needed")
    args = cli.parse_args()
    sys.exit(main(args.statement, args.parser, args.out, args.localities, args.names, args.also))
