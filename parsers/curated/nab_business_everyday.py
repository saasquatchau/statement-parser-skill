"""NAB Business Everyday Account statement Parser."""
import re
from datetime import datetime

from harness import MultipleAccounts
from harness.money import amount, balance

ISSUER = "NAB"
STATEMENT_FORMAT = "NAB Business Everyday Account statement"
ACCOUNT_TYPE = "deposit"
SIGNATURE = ["NAB Business Everyday Account", "Business Servicing Team", "Date Particulars Debits Credits Balance"]
# Rows leave the other amount column empty; the tag on each amount says which column it's printed in.
COLUMNS = ["Debits", "Credits"]

MONEY = r"[\d,]+\.\d{2}"
DATE_RE = re.compile(r"^(\d{1,2} [A-Z][a-z]{2} \d{4})(?: (.*))?$")
AMT_LINE_RE = re.compile(r"^(.*?)\.{2,}\s*(Debits|Credits):(" + MONEY + r")(?: " + MONEY + r" (?:Cr|Dr|CR|DR))?$")
OPEN_RE = re.compile(r"^Opening balance \$?(" + MONEY + r") (Cr|Dr|CR|DR)$")
CLOSE_RE = re.compile(r"^Closing balance \$?(" + MONEY + r") (Cr|Dr|CR|DR)$")
START_RE = re.compile(r"^Statement starts (\d{1,2} [A-Za-z]+ \d{4})")
END_RE = re.compile(r"^Statement ends (\d{1,2} [A-Za-z]+ \d{4})")
BSB_RE = re.compile(r"BSB number (\d{3}-\d{3})")
ACCT_RE = re.compile(r"Account number ([\d-]{6,})")
HOLDER_MARK_RE = re.compile(r"^/\d+$")
NOT_PARTICULARS = re.compile(r"^(Brought|Carried) forward ")


def _bal(num, suffix):
    return balance(num + " " + suffix.upper(), ACCOUNT_TYPE)


def _pdate(s):
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse(text):
    lines = [ln.strip() for ln in text.splitlines()]
    identifiers = {}
    accounts = set()
    start = end = None
    opening = closing = None
    in_table = done = False
    cur_date = None
    pending = []
    txns = []

    for i, ln in enumerate(lines):
        if not ln:
            continue
        if m := START_RE.match(ln):
            start = _pdate(m.group(1))
        if m := END_RE.match(ln):
            end = _pdate(m.group(1))
        if (m := OPEN_RE.match(ln)) and opening is None:
            opening = _bal(m.group(1), m.group(2))
        if (m := CLOSE_RE.match(ln)) and closing is None:
            closing = _bal(m.group(1), m.group(2))
        if m := BSB_RE.search(ln):
            identifiers["bsb"] = m.group(1)
        if m := ACCT_RE.search(ln):
            accounts.add(m.group(1))
            identifiers["account_number"] = m.group(1)
        if HOLDER_MARK_RE.match(ln) and "holder_name" not in identifiers and i + 1 < len(lines):
            identifiers["holder_name"] = lines[i + 1]
            addr = []
            for nxt in lines[i + 2:]:
                if not nxt or nxt.startswith("Outlet Details"):
                    break
                addr.append(nxt)
            identifiers["address"] = addr

        if ln.startswith("Date Particulars Debits Credits Balance"):
            in_table = True
            pending = []
            continue
        if not in_table or done:
            continue
        if ln.startswith("Summary of Government Charges"):
            done = True
            continue

        if (m := DATE_RE.match(ln)) and (d := _pdate(m.group(1))):
            cur_date = d
            ln = (m.group(2) or "").strip()
            if not ln:
                continue
        if NOT_PARTICULARS.match(ln):
            pending = []
            continue
        if m := AMT_LINE_RE.match(ln):
            prefix, column, printed = m.group(1).strip(), m.group(2), m.group(3)
            # A row's particulars are the line above its amount line and the text before the dot leader.
            description = " ".join(pending[-1:] + ([prefix] if prefix else []))
            value = amount(printed)
            txns.append({"date": cur_date, "description": description,
                         "amount": value if column == "Credits" else -value})
            pending = []
            continue
        pending.append(ln)

    if len(accounts) > 1:
        raise MultipleAccounts()

    return {
        "statement_period": (start, end),
        "identifiers": identifiers,
        "opening_balance": opening,
        "closing_balance": closing,
        "transactions": txns,
    }
