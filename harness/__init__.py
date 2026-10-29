"""Shared harness that Runs Parsers over statements and writes Xero CSVs (see ADR-0001).

A Parser is a Python module for exactly one Statement Format, defining:

- ISSUER: the bank or card provider, e.g. "ANZ"
- STATEMENT_FORMAT: human-readable name, e.g. "ANZ credit card"
- ACCOUNT_TYPE: "deposit" or "credit_card"
- SIGNATURE: issuer-level strings that identify the format (never client details)
- parse(text) returning:
    {"statement_period": (start date, end date),
     "identifiers": {"account_number": str, "bsb": str, "holder_name": str, "address": [str]},  # read at run time
     "opening_balance": Decimal, "closing_balance": Decimal,
     "transactions": [{"date": date or (day, month), "description": str, "amount": Decimal, "fx": str (optional)}]}
  Balances are in the account's own direction (funds held, or amount owed on a credit card); use
  harness.money.balance to read printed CR/DR suffixes and minus signs. Amounts are Money In positive, Money Out
  negative. A date printed without a year is a (day, month) pair; the harness takes the year from the period.
  Raise MultipleAccounts if the statement covers more than one account.

Everything else (Reconciliation, CSV writing, the summary) belongs to the harness.
"""


class MultipleAccounts(Exception):
    """Raised by a Parser when a statement covers more than one account, which v1 does not support."""

