"""Macquarie Savings Account statement Parser."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Macquarie"
STATEMENT_FORMAT = "Macquarie Savings Account"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["Macquarie Savings Account Statement", "Date Transaction Description Debits Credits Balance"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MON = "(" + "|".join(MONTHS) + ")"
MONEY = r"[\d,]*\.\d{2}"
BALANCE = rf"{MONEY}(?:CR|DR)?"
PERIOD = re.compile(r"From (\d{1,2} [A-Za-z]+ \d{4}) to (\d{1,2} [A-Za-z]+ \d{4})")
OPENING = re.compile(rf"^\d{{2}} {MON} Opening balance ({BALANCE})$")
CLOSING = re.compile(rf"^\d{{2}} {MON} Closing balance ({BALANCE})$")
ROW = re.compile(rf"^(\d{{2}}) {MON} (.+) ({MONEY}) ({BALANCE})$")
ACCOUNT_HEADING = "BSB Account No. Account Name"
ACCOUNT = re.compile(r"^(\d{6}) (\d+) (.+?) Macquarie Bank Limited$")
STATE_POSTCODE = re.compile(r"\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT) \d{4}$")


def _day(printed):
    return datetime.strptime(printed, "%d %B %Y").date()


def parse(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    period = opening = closing = previous = None
    identifiers = {"address": []}
    transactions = []
    for i, line in enumerate(lines):
        if period is None and (m := PERIOD.search(line)):
            period = (_day(m[1]), _day(m[2]))
        elif line == ACCOUNT_HEADING and i + 1 < len(lines) and (m := ACCOUNT.match(lines[i + 1])):
            identifiers["bsb"], identifiers["account_number"], identifiers["holder_name"] = m[1], m[2], m[3]
        elif line == identifiers.get("holder_name") and not identifiers["address"]:
            # The mailing block: the name again, then the address down to the state and postcode.
            for address_line in lines[i + 1:i + 4]:
                identifiers["address"].append(address_line)
                if STATE_POSTCODE.search(address_line):
                    break
        if m := OPENING.match(line):
            opening = previous = balance(m[2], ACCOUNT_TYPE)
        elif m := CLOSING.match(line):
            closing = balance(m[2], ACCOUNT_TYPE)
        elif m := ROW.match(line):
            value, new_balance = amount(m[4]), balance(m[5], ACCOUNT_TYPE)
            # One amount column: the running balance says whether it was a debit or a credit.
            signed = value if previous is not None and new_balance - previous == value else -value
            transactions.append({"date": (int(m[1]), MONTHS.index(m[2]) + 1), "description": m[3], "amount": signed})
            previous = new_balance
    return {
        "statement_period": period,
        "identifiers": identifiers,
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": transactions,
    }
