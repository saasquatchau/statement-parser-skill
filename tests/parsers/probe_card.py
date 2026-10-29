"""Synthetic Parser for the made-up Probe Card Services credit card Statement Format."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Probe Card Services"
STATEMENT_FORMAT = "Probe Card"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["PROBE CARD SERVICES", "Platinum Card Statement"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}/\d{2}/\d{4}) (.+) ([\d,]+\.\d{2}) (CR|DR)$")
CLOSING_LABEL = "Closing balance "


def day(s):
    return datetime.strptime(s, "%d/%m/%Y").date()


def parse(text):
    period = account = opening = closing = None
    transactions = []
    for line in text.splitlines():
        if m := PERIOD.match(line):
            period = (day(m[1]), day(m[2]))
        elif line.startswith("Account number "):
            account = line[len("Account number "):]
        elif line.startswith("Opening balance "):
            opening = balance(line[len("Opening balance "):], ACCOUNT_TYPE)
        elif line.startswith(CLOSING_LABEL):
            closing = balance(line[len(CLOSING_LABEL):], ACCOUNT_TYPE)
        elif m := ROW.match(line):
            transactions.append({
                "date": day(m[1]),
                "description": m[2],
                "amount": amount(m[3]) if m[4] == "CR" else -amount(m[3]),
            })
    return {"statement_period": period, "identifiers": {"account_number": account}, "opening_balance": opening, "closing_balance": closing, "transactions": transactions}
