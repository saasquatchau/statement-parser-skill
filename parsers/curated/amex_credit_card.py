"""American Express credit card statement Parser (current layout, 2026)."""
import re
from datetime import date

from harness.money import amount, balance

ISSUER = "American Express"
STATEMENT_FORMAT = "American Express credit card"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["American Express Credit Card", "Statement of Account", "Statement Period From"]

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
MONTH = "(" + "|".join(MONTHS) + ")"
MONEY = r"[\d,]*\.\d{2}"
PERIOD = re.compile(rf"Statement Period From {MONTH} ?(\d{{1,2}}) ?to ?{MONTH} ?(\d{{1,2}}), (\d{{4}})")
ROW = re.compile(rf"^{MONTH} ?(\d{{1,2}}) (.+) ({MONEY})$")
CURRENCY = re.compile(r"^[A-Z][A-Z .()-]*\b(DOLLAR|EURO|POUND|STERLIN\w*|YEN|FRANC|RUPEE|PESO|BAHT|WON|YUAN|RENMINBI|"
                      r"RINGGIT|DONG|KRONA|KRONE|KRONER|RAND|REAL|DIRHAM|SHEKEL|ZLOTY|FORINT|LIRA|RUPIAH|RIYAL|DINAR)\b")
CONVERSION = re.compile(r"^AUD [\d,]*\.\d{2} includes conversion commission")
SUMMARY_HEADING = "OPENING BALANCE NEW CREDITS NEW DEBITS CLOSING BALANCE"
TOTAL_HEADING = "CREDIT LIMIT $ AVAILABLE CREDIT $ TOTAL BALANCE $"
MEMBER_HEADING = "Prepared for Membership Number"
MEMBER = re.compile(r"^(.+?) ([Xx]{4}-[Xx]{6}-\d{5})\b")


def _period(m):
    end_year = int(m[5])
    start_month, end_month = MONTHS.index(m[1]) + 1, MONTHS.index(m[3]) + 1
    start_year = end_year - 1 if start_month > end_month else end_year
    return date(start_year, start_month, int(m[2])), date(end_year, end_month, int(m[4]))


def _opening(printed_opening, credits, debits, closing):
    """The summary prints the opening balance without saying whether it is in credit; the statement's own
    arithmetic (opening - credits + debits = closing, as amount owed) settles it."""
    owed = amount(printed_opening)
    return owed if owed - credits + debits == closing else -owed


def _add_fx(transaction, line):
    """Currency and conversion lines follow a foreign transaction. The foreign amount is the last token of the
    row's description, so it moves into the FX prose."""
    if "fx" not in transaction:
        description, _, foreign = transaction["description"].rpartition(" ")
        transaction["description"], transaction["fx"] = description, foreign
    transaction["fx"] += " " + line


def parse(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    period = summary = closing = None
    identifiers = {"address": []}
    transactions = []
    in_row = False  # True from a transaction row until the next line that isn't one of its detail lines
    for i, line in enumerate(lines):
        if m := PERIOD.search(line):
            period = _period(m)
        elif line.startswith(MEMBER_HEADING) and i + 1 < len(lines) and (m := MEMBER.match(lines[i + 1])):
            identifiers["holder_name"], identifiers["account_number"] = m[1], m[2]
        elif line == SUMMARY_HEADING:
            summary = lines[i + 1].split()
        elif line == TOTAL_HEADING:
            closing = balance(lines[i + 1].split()[-1].replace("CR", " CR"), ACCOUNT_TYPE)
        elif line.startswith("PAYMENT ADVICE"):
            # The payment slip ends the first page: name, then two address lines.
            identifiers["address"] = lines[i + 2:i + 4]
        if in_row and line == "CR":
            transactions[-1]["amount"] = -transactions[-1]["amount"]
            continue
        if in_row and (CURRENCY.match(line) or CONVERSION.match(line)):
            _add_fx(transactions[-1], line)
            continue
        m = ROW.match(line)
        in_row = bool(m)
        if m:
            transactions.append({
                "date": (int(m[2]), MONTHS.index(m[1]) + 1),
                "description": m[3],
                # Charges are Money Out; a CR on the next line turns the row into Money In.
                "amount": -amount(m[4]),
            })
    opening, credits, debits, _ = summary
    return {
        "statement_period": period,
        "identifiers": identifiers,
        "opening_balance": _opening(opening, amount(credits), amount(debits), closing),
        "closing_balance": closing,
        "transactions": transactions,
    }
