"""Westpac Choice electronic statement Parser."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "Westpac"
STATEMENT_FORMAT = "Westpac Choice electronic statement"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["Westpac Banking Corporation", "Electronic Statement", "STATEMENT OPENING BALANCE"]

MONEY = r"-?\d{1,3}(?:,\d{3})*\.\d{2}"
DATE_RE = re.compile(r"^(\d{2}/\d{2}/\d{2})\b\s*(.*)$")
TAIL_RE = re.compile(r"^(.*?)\s*(" + MONEY + r")\s+(" + MONEY + r")$")
HEADER = "DATE TRANSACTION DESCRIPTION DEBIT CREDIT BALANCE"


def _summary(text, label):
    m = re.search(label + r"\s*([+-])\s*\$\s*(" + MONEY + ")", text)
    if not m:
        raise ValueError("missing " + label)
    val = m.group(2)
    return balance(("-" if m.group(1) == "-" else "") + val, ACCOUNT_TYPE)


def _identifiers(lines):
    ids = {}
    for i, ln in enumerate(lines):
        if ln.strip() == "BSB Account Number" and i + 1 < len(lines):
            m = re.match(r"^(\S+)\s+(\S+)$", lines[i + 1].strip())
            if m:
                ids["bsb"], ids["account_number"] = m.group(1), m.group(2)
            break
    for i, ln in enumerate(lines):
        if ln.strip() == "Name" and i + 1 < len(lines):
            ids["holder_name"] = lines[i + 1].strip()
            addr = []
            for nxt in lines[i + 2:]:
                s = nxt.strip()
                if s.startswith("BSB"):
                    break
                s = re.sub(r"\s*Card Number$", "", s)
                if re.match(r"^[\d*\s]+$", s) and "*" in s:
                    continue
                if s:
                    addr.append(s.rstrip(","))
            ids["address"] = addr
            break
    return ids


def parse(text):
    if len(set(re.findall(r"BSB Account Number\n(\S+ \S+)", text))) > 1:
        raise MultipleAccounts()
    lines = text.splitlines()
    m = re.search(r"Statement Period\s*\n\s*(\d{1,2} \w+ \d{4})\s*-\s*(\d{1,2} \w+ \d{4})", text)
    start = datetime.strptime(m.group(1), "%d %B %Y").date()
    end = datetime.strptime(m.group(2), "%d %B %Y").date()

    opening = _summary(text, "Opening Balance")
    closing = _summary(text, "Closing Balance")

    txns = []
    prev_bal = None
    cur = None  # [date, [desc parts]]
    in_table = False
    for raw in lines:
        ln = raw.strip()
        if ln == HEADER:
            in_table = True
            continue
        if not in_table:
            continue
        if ln.startswith("Westpac Banking Corporation") or ln.startswith("CONVENIENCE AT YOUR"):
            in_table = False
            cur = None
            continue
        if not ln:
            continue
        dm = DATE_RE.match(ln)
        if dm:
            rest = dm.group(2)
            if "OPENING BALANCE" in rest:
                prev_bal = amount(re.findall(MONEY, rest)[-1])
                cur = None
                continue
            if "CLOSING BALANCE" in rest:
                cur = None
                continue
            d = datetime.strptime(dm.group(1), "%d/%m/%y").date()
            cur = [d, []]
            ln = rest
            if not ln:
                continue
        if cur is None:
            continue
        tm = TAIL_RE.match(ln)
        if tm:
            if tm.group(1):
                cur[1].append(tm.group(1))
            amt = amount(tm.group(2))
            bal = amount(tm.group(3))
            if prev_bal is not None and bal < prev_bal:
                amt = -amt
            txns.append({"date": cur[0], "description": " ".join(cur[1]).strip(), "amount": amt})
            prev_bal = bal
            cur = None
        else:
            cur[1].append(ln)

    return {
        "statement_period": (start, end),
        "identifiers": _identifiers(lines),
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": txns,
    }
