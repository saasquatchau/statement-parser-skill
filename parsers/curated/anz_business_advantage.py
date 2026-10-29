"""ANZ Business Advantage statement Parser."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "ANZ"
STATEMENT_FORMAT = "ANZ Business Advantage statement"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["Australia and New Zealand Banking Group Limited", "BUSINESS ADVANTAGE STATEMENT"]

MONTHS = {m: i for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}

PERIOD_RE = re.compile(r"^(\d{1,2} [A-Z]+ \d{4}) TO (\d{1,2} [A-Z]+ \d{4})$")
ROW_RE = re.compile(r"^(\d{2}) (JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) (.+)$")
MONEY = r"[\d,]+\.\d{2}"
AMT_RE = re.compile(r"^(?:" + MONEY + r"|blank)$")
BAL_RE = re.compile(r"^" + MONEY + r"(?:CR|DR)?$")
ACCT_RE = re.compile(r"^Account Number (\d{3,}-\d{3,})$")
BSB_RE = re.compile(r"^(\d{3}-\d{3}) ")
OPEN_RE = re.compile(r"OPENING BALANCE (" + MONEY + r"\s?(?:CR|DR)?)$")
END_RE = re.compile(r"^TOTALS AT END OF PERIOD \$?(" + MONEY + r") \$?(" + MONEY + r") \$?(" + MONEY + r"\s?(?:CR|DR)?)$")

STOP_PREFIXES = (
    "PAGE ", "Page ", "BUSINESS ADVANTAGE STATEMENT", "Account Number", "Transaction Details",
    "Please retain", "Date Transaction Details", "blank ", "TOTALS AT END", "This Statement Includes",
)


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
                addr.append(nxt)
            if addr:
                identifiers["holder_name"] = addr[0]
                identifiers["address"] = addr[1:]
            continue
        m = ACCT_RE.match(ln)
        if m:
            accounts.add(m.group(1))
            identifiers["account_number"] = m.group(1)
        if ln == "Account Number" and i + 1 < len(lines):
            nxt = lines[i + 1]
            if re.match(r"^\d{3,}-\d{3,}$", nxt):
                accounts.add(nxt)
                identifiers["account_number"] = nxt
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
            mo = OPEN_RE.search(rest)
            if mo and rest.startswith("OPENING BALANCE"):
                if opening is None:
                    opening = balance(mo.group(1), ACCOUNT_TYPE)
                current = None
                continue
            parts = _split_row(rest)
            if parts:
                desc, wd, dep = parts
                if wd != "blank":
                    amt = -amount(wd)
                else:
                    amt = amount(dep)
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
