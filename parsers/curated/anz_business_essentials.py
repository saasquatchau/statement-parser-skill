"""ANZ Business Essentials (business transaction account) statement Parser."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "ANZ"
STATEMENT_FORMAT = "ANZ Business Essentials"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["ANZ BUSINESS ESSENTIALS STATEMENT", "Transaction Details"]

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MON = "(" + "|".join(MONTHS) + ")"
MONEY = r"[\d,]*\.\d{2}"
CELL = rf"({MONEY}|blank)"  # empty table cells are printed as the word "blank"
PERIOD = re.compile(r"^(\d{1,2} [A-Z]+ \d{4}) TO (\d{1,2} [A-Z]+ \d{4})$")
OPENING = re.compile(rf"^\d{{1,2}} {MON} OPENING BALANCE ({MONEY}(?: DR)?)$")
ROW = re.compile(rf"^(\d{{1,2}}) {MON} (.+?) {CELL} {CELL} ({MONEY}(?: DR)?)$")
ACCOUNT = re.compile(r"^Account Number (\d{4}-\d{5,})$")
CLOSING = re.compile(rf"^TOTALS AT END OF PERIOD \$?{MONEY} \$?{MONEY} \$?({MONEY}(?: DR)?)$")
NOT_DESCRIPTION = re.compile(r"^(blank\b|TOTALS\b|Date Transaction|\d{4} blank|Account Number|ANZ BUSINESS|Page \d|"
                             r"Transaction Details|Please retain|IMPORTANT INFORMATION)")


def _day(printed):
    return datetime.strptime(printed.title(), "%d %B %Y").date()


def parse(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    period = opening = closing = None
    identifiers = {"address": []}
    transactions = []
    in_row = False
    for i, line in enumerate(lines):
        if m := PERIOD.match(line):
            period = (_day(m[1]), _day(m[2]))
            # The mailing block follows the period: an attention line, then the address up to the country.
            block = lines[i + 1:lines.index("AUSTRALIA", i)] if "AUSTRALIA" in lines[i:] else []
            identifiers["address"] = block[1:]
        elif line == "Opening Balance:" and i + 1 < len(lines):
            identifiers["holder_name"] = lines[i + 1]
        elif line.startswith("Branch Number (BSB)") and i + 1 < len(lines):
            identifiers["bsb"] = lines[i + 1].split()[0]
        elif m := ACCOUNT.match(line):
            # Page 1 prints its details in interleaved columns; the per-page header has the number on one line.
            identifiers["account_number"] = m[1]
        if m := OPENING.match(line):
            opening = balance(m[2], ACCOUNT_TYPE)
            in_row = False
        elif m := ROW.match(line):
            withdrawal, deposit = m[4], m[5]
            transactions.append({
                "date": (int(m[1]), MONTHS.index(m[2]) + 1),
                "description": m[3],
                "amount": amount(deposit) if deposit != "blank" else -amount(withdrawal),
            })
            in_row = True
        elif m := CLOSING.match(line):
            closing = balance(m[1], ACCOUNT_TYPE)
            in_row = False
        elif in_row and not NOT_DESCRIPTION.match(line) and not re.search(MONEY, line):
            # A long description wraps onto the next line, with no date or amounts of its own.
            transactions[-1]["description"] += " " + line
        else:
            in_row = False
    return {
        "statement_period": period,
        "identifiers": identifiers,
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": transactions,
    }
