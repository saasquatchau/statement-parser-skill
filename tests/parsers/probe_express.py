"""Synthetic Parser for a made-up Amex-style card that prints foreign-currency detail lines under a transaction."""
import re
from datetime import datetime

from harness.money import amount, balance

ISSUER = "Probe Express"
STATEMENT_FORMAT = "Probe Express"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["PROBE EXPRESS", "Card Statement"]

PERIOD = re.compile(r"^Statement period (\d{2}/\d{2}/\d{4}) to (\d{2}/\d{2}/\d{4})$")
ROW = re.compile(r"^(\d{2}/\d{2}/\d{4}) (.+) (-?[\d,]+\.\d{2})$")


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
            printed = m[3]
            value = amount(printed.lstrip("-"))
            transactions.append({"date": day(m[1]), "description": m[2],
                                 "amount": value if printed.startswith("-") else -value})
        elif transactions and line and line not in SIGNATURE:
            # Conversion detail lines belong to the transaction above; they are never rows of their own.
            previous = transactions[-1]
            previous["fx"] = f"{previous['fx']} {line}" if "fx" in previous else line
    return {"statement_period": period, "identifiers": {"account_number": account}, "opening_balance": opening, "closing_balance": closing,
            "transactions": transactions}
