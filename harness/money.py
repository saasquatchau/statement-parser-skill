"""Reads printed amounts and balances for Parsers, so every Parser handles signs the same way."""
import re
from decimal import Decimal

_BALANCE = re.compile(r"^\s*(-)?\$?([\d,]+\.\d{2})\s*(CR|DR)?\s*$", re.IGNORECASE)


def amount(printed):
    """An unsigned printed amount such as "1,234.56"."""
    return Decimal(printed.replace(",", "").replace("$", "").strip())


def balance(printed, account_type):
    """A printed balance in the account's own direction: funds held for a deposit account, the amount owed for a
    credit card. Crossing zero shows as a minus sign, or as DR on a deposit account and CR on a credit card."""
    m = _BALANCE.match(printed)
    if not m:
        raise ValueError("unrecognised balance")
    value = amount(m[2])
    suffix = (m[3] or "").upper()
    below_zero = m[1] or suffix == ("DR" if account_type == "deposit" else "CR")
    return -value if below_zero else value
