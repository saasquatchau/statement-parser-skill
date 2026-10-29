"""Synthetic Parser for a made-up ANZ-style card that prints debits and credits in separate tables."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Probe Split"
STATEMENT_FORMAT = "Probe Split Card"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["PROBE SPLIT CARD"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}/\d{2}/\d{4}) (.+) ([\d,]+\.\d{2})$")


def day(s):
    return datetime.strptime(s, "%d/%m/%Y").date()


def parse(text):
    period = account = opening = closing = None
    sign = None
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
        elif line == "Purchases and debits":
            sign = -1
        elif line == "Payments and credits":
            sign = 1
        elif m := ROW.match(line):
            transactions.append({"date": day(m[1]), "description": m[2], "amount": sign * amount(m[3])})
    return {"statement_period": period, "identifiers": {"account_number": account}, "opening_balance": opening, "closing_balance": closing,
            "transactions": transactions}
