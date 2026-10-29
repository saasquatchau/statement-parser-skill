"""CommBank Business Transaction Account statement Parser."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "Commonwealth Bank"
STATEMENT_FORMAT = "CommBank Business Transaction Account"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["Business Transaction Account", "Date Transaction Debit Credit Balance", "commbank.com.au"]

MONEY = r"\d{1,3}(?:,\d{3})*\.\d{2}"
PERIOD_RE = re.compile(r"Period\s*(\d{1,2}[A-Za-z]{3}\d{4})\s*-\s*(\d{1,2}[A-Za-z]{3}\d{4})")
ACCT_RE = re.compile(r"^AccountNumber\s+(\d[\d ]*\d)\s*$")
NAME_RE = re.compile(r"^Name\s+(.+)$")
OPEN_RE = re.compile(r"^\d{1,2}[A-Za-z]{3}\s*\d{4}\s*OPENING\s*BALANCE\s+(" + MONEY + r")\s*(CR|DR)?\s*$")
CLOSE_RE = re.compile(r"^\d{1,2}[A-Za-z]{3}\s*\d{4}\s*CLOSING\s*BALANCE\s+(" + MONEY + r")\s*(CR|DR)?\s*$")
START_RE = re.compile(r"^(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(.*)$")
END_RE = re.compile(r"^(.*?)\s*(" + MONEY + r")\s+(" + MONEY + r")\s*(CR|DR)?\s*$")
VALUE_DATE_RE = re.compile(r"\s*ValueDate\s+\d{2}/\d{2}/\d{4}\s*")
SKIP_RE = re.compile(r"^(PAGE \d+ of \d+|Statement\s*\d+\s*Page|AccountNumber|Date Transaction Debit Credit Balance)")
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def _d(s):
    return datetime.strptime(s, "%d%b%Y").date()


def parse(text):
    lines = [l.strip() for l in text.splitlines()]
    period = None
    accounts = set()
    holder = None
    opening = closing = None
    txns = []
    pending = None
    prev_bal = None

    for line in lines:
        if not line:
            continue
        m = PERIOD_RE.search(line)
        if m and period is None:
            period = (_d(m.group(1)), _d(m.group(2)))
            continue
        m = ACCT_RE.match(line)
        if m:
            accounts.add(m.group(1).replace(" ", ""))
            pending = None if pending is None else pending
            continue
        m = NAME_RE.match(line)
        if m and holder is None:
            holder = m.group(1).strip()
            continue
        m = OPEN_RE.match(line)
        if m and opening is None:
            opening = balance(m.group(1) + (m.group(2) or ""), ACCOUNT_TYPE)
            prev_bal = opening
            pending = None
            continue
        m = CLOSE_RE.match(line)
        if m:
            closing = balance(m.group(1) + (m.group(2) or ""), ACCOUNT_TYPE)
            pending = None
            continue
        if opening is None or closing is not None:
            continue
        if SKIP_RE.match(line):
            continue

        m = START_RE.match(line)
        if m and pending is None:
            pending = {"day": int(m.group(1)), "month": MONTHS[m.group(2)], "parts": []}
            rest = m.group(3)
        elif pending is not None:
            rest = line
        else:
            continue

        e = END_RE.match(rest)
        if e:
            if e.group(1):
                pending["parts"].append(e.group(1))
            amt = amount(e.group(2))
            new_bal = balance(e.group(3) + (e.group(4) or ""), ACCOUNT_TYPE)
            signed = amt if new_bal - prev_bal == amt else -amt
            desc = " ".join(pending["parts"])
            desc = VALUE_DATE_RE.sub(" ", desc)
            desc = re.sub(r"\s+", " ", desc).strip()
            txns.append({"date": (pending["day"], pending["month"]), "description": desc, "amount": signed})
            prev_bal = new_bal
            pending = None
        else:
            pending["parts"].append(rest)

    if len(accounts) > 1:
        raise MultipleAccounts("statement covers several accounts")

    return {
        "statement_period": period,
        "identifiers": {
            "account_number": next(iter(accounts)) if accounts else None,
            "holder_name": holder,
        },
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": txns,
    }
