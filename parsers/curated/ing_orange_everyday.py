"""ING Orange Everyday (transaction account) statement Parser."""
import re
from datetime import datetime

from harness.money import balance

ISSUER = "ING"
STATEMENT_FORMAT = "ING Orange Everyday"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["Orange Everyday", "Statement from:", "Money out $ Money in $ Balance $"]

DATE = r"\d{2}/\d{2}/\d{4}"
SIGNED = r"-?[\d,]*\.\d{2}"
PERIOD = re.compile(rf"^Statement from: ({DATE}) to ({DATE})$")
SUMMARY_HEADING = "Opening balance Total money in Total money out Closing balance"
ROW = re.compile(rf"^({DATE}) (.+) ({SIGNED}) ({SIGNED})$")
HOLDER = re.compile(r"^(.+?) Orange Everyday number: (\d+)$")
STATE_POSTCODE = re.compile(r"\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT) \d{4}$")
NOT_DESCRIPTION = re.compile(r"^(Page \d|Total |\d+-[ISE]$|Transactions|Date Details|Please check|Account name:)")


def _day(printed):
    return datetime.strptime(printed, "%d/%m/%Y").date()


def _balance(printed):
    # Printed as "$-12.00" when negative.
    return balance(printed.replace("$", ""), ACCOUNT_TYPE)


def parse(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    period = opening = closing = None
    identifiers = {"address": []}
    transactions = []
    in_row = False
    for i, line in enumerate(lines):
        if m := PERIOD.match(line):
            period = (_day(m[1]), _day(m[2]))
        elif line.startswith("BSB number: "):
            identifiers["bsb"] = line[len("BSB number: "):]
        elif m := HOLDER.match(line):
            identifiers["holder_name"], identifiers["account_number"] = m[1], m[2]
            # The address follows the name, interleaved with statement details, and ends at the state and postcode.
            for address_line in lines[i + 1:i + 6]:
                if not address_line.startswith("Statement "):
                    identifiers["address"].append(address_line)
                if STATE_POSTCODE.search(address_line):
                    break
        elif line == SUMMARY_HEADING:
            values = lines[i + 1].split()
            opening, closing = _balance(values[0]), _balance(values[-1])
        if m := ROW.match(line):
            transactions.append({"date": _day(m[1]), "description": m[2], "amount": balance(m[3], ACCOUNT_TYPE)})
            in_row = True
        elif in_row and not NOT_DESCRIPTION.match(line):
            # Merchant, location and card details print on the lines below each row.
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
