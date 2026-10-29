"""Writes reconciled statements as Xero CSVs, one per account per batch (or per statement), and flags
identical rows without removing them."""
import csv
import re
from collections import defaultdict

XERO_HEADER = ["*Date", "*Amount", "Payee", "Description", "Reference"]
ACCOUNT_TYPE_CODES = {"deposit": "DEP", "credit_card": "CC"}
MAX_LISTED_DUPLICATES = 5


def description(t):
    # Foreign-currency conversion prose is kept verbatim after the printed transaction text.
    return f"{t['description']} {t['fx']}" if t.get("fx") else t["description"]


def xero_row(t):
    return [t["date"].strftime("%d/%m/%Y"), f"{t['amount']:.2f}", "", description(t), ""]


def account_key(parser, result):
    last4 = re.sub(r"\D", "", result["identifiers"]["account_number"])[-4:]
    return parser.ISSUER, parser.ACCOUNT_TYPE, last4


def csv_name(key, statements):
    issuer, account_type, last4 = key
    start = min(r["statement_period"][0] for _, r in statements).strftime("%Y-%m")
    end = max(r["statement_period"][1] for _, r in statements).strftime("%Y-%m")
    period = start if start == end else f"{start}-to-{end}"
    return f"{re.sub(r'[^A-Za-z0-9]+', '-', issuer)}-{ACCOUNT_TYPE_CODES[account_type]}-xx{last4}-{period}.csv"


def group(reconciled, per_statement):
    """`reconciled` is a list of (parser, result); returns {csv name: [(parser, result), ...]} in batch order."""
    groups = defaultdict(list)
    for i, (parser, result) in enumerate(reconciled):
        groups[(account_key(parser, result), i if per_statement else None)].append((parser, result))
    return {csv_name(key, statements): statements for (key, _), statements in groups.items()}


def write_csv(path, statements):
    """Writes one CSV; returns its rows (without the header) for the duplicate check."""
    ordered = sorted(statements, key=lambda s: s[1]["statement_period"][0])
    # Python's sort is stable, so printed order survives within each date.
    transactions = sorted((t for _, r in ordered for t in r["transactions"]), key=lambda t: t["date"])
    rows = [xero_row(t) for t in transactions]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(XERO_HEADER)
        writer.writerows(rows)
    return rows


def duplicate_warning(rows):
    """Describes sets of identical rows by spreadsheet row number, date and amount only (never the description,
    which is statement content). Returns None when there are none."""
    seen = defaultdict(list)
    for number, row in enumerate(rows, start=2):  # row 1 is the header
        seen[tuple(row)].append(number)
    sets = [(numbers, row) for row, numbers in seen.items() if len(numbers) > 1]
    if not sets:
        return None
    listed = [f"rows {'/'.join(map(str, numbers))} {row[0]} {row[1]}" for numbers, row in sets[:MAX_LISTED_DUPLICATES]]
    if len(sets) > MAX_LISTED_DUPLICATES:
        listed.append(f"+{len(sets) - MAX_LISTED_DUPLICATES} more")
    return f"{len(sets)} set{'s' if len(sets) > 1 else ''} of identical rows ({'; '.join(listed)}). Check before importing."
