"""Synthetic Parser for a made-up Probe Bank layout that leaves the unused amount column empty, so only the
column an amount sits under says whether it's money in or out."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Probe Bank"
STATEMENT_FORMAT = "Probe Bank columns"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["PROBE BANK", "Columns Account Statement"]
COLUMNS = ["Debits", "Credits"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}/\d{2}/\d{4}) (.+) (Debits|Credits):([\d,]+\.\d{2}) [\d,]+\.\d{2}$")


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
            value = amount(m[4])
            transactions.append({"date": day(m[1]), "description": m[2],
                                 "amount": value if m[3] == "Credits" else -value})
    return {"statement_period": period, "identifiers": {"account_number": account}, "opening_balance": opening,
            "closing_balance": closing, "transactions": transactions}
