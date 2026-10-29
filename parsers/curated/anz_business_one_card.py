"""ANZ Business One credit card statement Parser."""
import re
from datetime import date

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "ANZ"
STATEMENT_FORMAT = "ANZ Business One credit card statement"
ACCOUNT_TYPE = "credit_card"
SIGNATURE = ["ANZ BUSINESS ONE", "YOUR ANZ ACCOUNT SUMMARY", "Purchases, Cash Advances & Other Debits"]

MONEY = r"[\d,]+\.\d{2}"
PERIOD_RE = re.compile(r"STATEMENT PERIOD: (\d{2})/(\d{2})/(\d{2,4}) to (\d{2})/(\d{2})/(\d{2,4})")
ACCT_RE = re.compile(r"ACCOUNT NUMBER: ([\d-]{8,})", re.I)
OPEN_RE = re.compile(r"^Opening (?:Account )?Balance \$?(" + MONEY + r"(?:\s?(?:CR|DR))?)$", re.I)
CLOSE_RE = re.compile(r"^Closing (?:Account )?Balance \$?(" + MONEY + r"(?:\s?(?:CR|DR))?)$", re.I)
ROW_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{4}) (.+)$")
AMT_RE = re.compile(r"^" + MONEY + r"(?:CR)?$")
GST_RE = re.compile(r"^(?:" + MONEY + r"|blank)$")


def _d(dd, mm, yy):
    y = int(yy)
    if y < 100:
        y += 2000
    return date(y, int(mm), int(dd))


def _split(rest):
    toks = rest.split(" ")
    if len(toks) >= 3 and AMT_RE.match(toks[-2]) and GST_RE.match(toks[-1]):
        return " ".join(toks[:-2]), toks[-2]
    if len(toks) >= 2 and AMT_RE.match(toks[-1]):
        return " ".join(toks[:-1]), toks[-1]
    return None


def parse(text):
    lines = [ln.strip() for ln in text.splitlines()]
    period = None
    identifiers = {}
    accounts = set()
    opening = closing = None
    txns = []

    for i, ln in enumerate(lines):
        if not ln:
            continue
        m = PERIOD_RE.search(ln)
        if m and period is None:
            g = m.groups()
            period = (_d(*g[0:3]), _d(*g[3:6]))
            continue
        m = ACCT_RE.search(ln)
        if m:
            acct = m.group(1)
            accounts.add(acct.replace("-", ""))
            identifiers.setdefault("account_number", acct)
        if ln.startswith("Cards Enquiries") and "holder_name" not in identifiers:
            block = []
            for nxt in lines[i + 1:]:
                if not nxt:
                    break
                stop = "PAYMENT SUMMARY" in nxt
                cleaned = nxt.replace("PAYMENT SUMMARY", "").strip()
                if cleaned:
                    block.append(cleaned)
                if stop:
                    break
            if block:
                identifiers["holder_name"] = block[0]
                identifiers["address"] = block[1:]
            continue
        m = OPEN_RE.match(ln)
        if m:
            if opening is None:
                opening = balance(m.group(1), ACCOUNT_TYPE)
            continue
        m = CLOSE_RE.match(ln)
        if m:
            closing = balance(m.group(1), ACCOUNT_TYPE)
            continue
        m = ROW_RE.match(ln)
        if m:
            parts = _split(m.group(4))
            if parts:
                desc, amt_s = parts
                if amt_s.endswith("CR"):
                    amt = amount(amt_s[:-2])
                else:
                    amt = -amount(amt_s)
                txns.append({"date": _d(m.group(1), m.group(2), m.group(3)), "description": desc, "amount": amt})

    if len(accounts) > 1:
        raise MultipleAccounts()

    return {
        "statement_period": period,
        "identifiers": identifiers,
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": txns,
    }
