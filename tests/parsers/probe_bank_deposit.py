"""Synthetic Parser for the made-up Probe Bank deposit Statement Format, used by the harness tests."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "Probe Bank"
STATEMENT_FORMAT = "Probe Bank deposit"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["PROBE BANK", "Everyday Account Statement"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}/\d{2}/\d{4}) (.+) ([\d,]+\.\d{2}) (CR|DR)$")


def day(s):
    return datetime.strptime(s, "%d/%m/%Y").date()


def parse(text):
    period = account = holder = address = opening = closing = None
    transactions = []
    for line in text.splitlines():
        if m := PERIOD.match(line):
            period = (day(m[1]), day(m[2]))
        elif line.startswith("Account number "):
            account = line[len("Account number "):]
        elif line.startswith("Account holder "):
            holder = line[len("Account holder "):]
        elif line.startswith("Address "):
            address = line[len("Address "):]
        elif line.startswith("Opening balance "):
            if opening is not None:
                raise MultipleAccounts()
            opening = balance(line[len("Opening balance "):], ACCOUNT_TYPE)
        elif line.startswith("Closing balance "):
            closing = balance(line[len("Closing balance "):], ACCOUNT_TYPE)
        elif m := ROW.match(line):
            value = amount(m[3])
            transactions.append({
                "date": day(m[1]),
                "description": m[2],
                "amount": value if m[4] == "CR" else -value,
            })
    return {"statement_period": period, "identifiers": {"account_number": account, "holder_name": holder,
                                                       "address": [address] if address else []}, "opening_balance": opening, "closing_balance": closing, "transactions": transactions}
