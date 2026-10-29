"""Synthetic Parser for a made-up store card that prints transaction dates without a year."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Probe Store"
STATEMENT_FORMAT = "Probe Store Card"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["PROBE STORE CARD"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}) (\w{3}) (.+) (-?[\d,]+\.\d{2})$")
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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
        elif line.startswith("Closing balance "):
            closing = balance(line[len("Closing balance "):], ACCOUNT_TYPE)
        elif m := ROW.match(line):
            printed = m[4]
            # Purchases print positive (owed goes up), refunds negative: Money In is the opposite sign.
            value = amount(printed.lstrip("-"))
            transactions.append({
                "date": (int(m[1]), MONTHS.index(m[2]) + 1),
                "description": m[3],
                "amount": value if printed.startswith("-") else -value,
            })
    return {"statement_period": period, "identifiers": {"account_number": account}, "opening_balance": opening, "closing_balance": closing,
            "transactions": transactions}
