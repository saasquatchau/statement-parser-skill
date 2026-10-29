"""ANZ Business Classic with Business Overdraft statement Parser."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "ANZ"
STATEMENT_FORMAT = "ANZ Business Classic with Business Overdraft statement"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["ANZ ACCOUNT AT A GLANCE", "BUSINESS CLASSIC STATEMENT WITH BUSINESS", "OVERDRAFT FACILITY"]

MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

PERIOD_RE = re.compile(r"^(\d{1,2} [A-Z]+ \d{4}) TO (\d{1,2} [A-Z]+ \d{4})$")
ROW_RE = re.compile(r"^(\d{2}) (JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) (.+)$")
MONEY = r"[\d,]+\.\d{2}"
AMT_RE = re.compile(r"^(?:" + MONEY + r"|blank)$")
BAL_RE = re.compile(r"^" + MONEY + r"(?:CR|DR)?$")
ACCT_RE = re.compile(r"Account Number (\d{3,}-\d{3,})$")
ACCT_ONLY_RE = re.compile(r"^\d{3,}-\d{3,}$")
BSB_RE = re.compile(r"^(\d{3}-\d{3}) ")
OPEN_RE = re.compile(r"^OPENING BALANCE (" + MONEY + r"\s?(?:CR|DR)?)$")
END_RE = re.compile(r"^TOTALS AT END OF PERIOD \$?(" + MONEY + r") \$?(" + MONEY + r") \$?(" + MONEY + r"\s?(?:CR|DR)?)$")

STOP_PREFIXES = (
    "PAGE ", "Page ", "BUSINESS CLASSIC STATEMENT", "OVERDRAFT FACILITY", "Account Number",
    "Transaction Details", "Please retain", "Date Transaction Details", "blank ", "TOTALS AT END",
    "This Statement Includes", "Interest Rate Table",
)
NOT_ADDRESS = ("OVERDRAFT INFORMATION", "Overdraft Limit", "Limit Used", "Available Credit", "***")


def _date(s):
    return datetime.strptime(s.title(), "%d %B %Y").date()


def _split_row(rest):
    toks = rest.split(" ")
    if len(toks) >= 4 and AMT_RE.match(toks[-3]) and AMT_RE.match(toks[-2]) and BAL_RE.match(toks[-1]):
        return " ".join(toks[:-3]), toks[-3], toks[-2]
    if len(toks) >= 3 and AMT_RE.match(toks[-2]) and AMT_RE.match(toks[-1]) and "blank" in toks[-2:]:
        return " ".join(toks[:-2]), toks[-2], toks[-1]
    return None


def parse(text):
    lines = [ln.strip() for ln in text.splitlines()]
    period = None
    identifiers = {}
    opening = closing = None
    txns = []
    current = None
    accounts = set()

    for i, ln in enumerate(lines):
        if not ln:
            continue
        m = PERIOD_RE.match(ln)
        if m and period is None:
            period = (_date(m.group(1)), _date(m.group(2)))
            addr = []
            for nxt in lines[i + 1:]:
                if not nxt or nxt.startswith("WELCOME"):
                    break
                if not nxt.startswith(NOT_ADDRESS):
                    addr.append(nxt)
            identifiers["address"] = addr
            continue
        if ln == "Opening Balance:" and "holder_name" not in identifiers and i + 1 < len(lines):
            identifiers["holder_name"] = lines[i + 1]
        m = ACCT_RE.search(ln)
        if m:
            accounts.add(m.group(1))
            identifiers["account_number"] = m.group(1)
        if ln == "Account Number" and i + 1 < len(lines) and ACCT_ONLY_RE.match(lines[i + 1]):
            accounts.add(lines[i + 1])
            identifiers["account_number"] = lines[i + 1]
        if ln.startswith("Branch Number (BSB)") and i + 1 < len(lines):
            mb = BSB_RE.match(lines[i + 1])
            if mb:
                identifiers["bsb"] = mb.group(1)

        m = END_RE.match(ln)
        if m:
            closing = balance(m.group(3), ACCOUNT_TYPE)
            current = None
            continue

        m = ROW_RE.match(ln)
        if m:
            day, mon, rest = int(m.group(1)), MONTHS[m.group(2)], m.group(3)
            mo = OPEN_RE.match(rest)
            if mo:
                if opening is None:
                    opening = balance(mo.group(1), ACCOUNT_TYPE)
                current = None
                continue
            parts = _split_row(rest)
            if parts:
                desc, wd, dep = parts
                amt = -amount(wd) if wd != "blank" else amount(dep)
                current = {"date": (day, mon), "description": desc, "amount": amt}
                txns.append(current)
                continue

        if ln.startswith(STOP_PREFIXES) or re.match(r"^\d{4} blank blank$", ln):
            current = None
            continue
        if current is not None and not ln.startswith("EFFECTIVE DATE"):
            current["description"] = current["description"] + " " + ln

    if len(accounts) > 1:
        raise MultipleAccounts()

    return {
        "statement_period": period,
        "identifiers": identifiers,
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": txns,
    }
