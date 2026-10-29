# Writing a Parser

Read this only during a Build. A Parser is one Python module for exactly one Statement Format (one printed layout from one issuer). It only describes the layout; the harness does everything else (Reconciliation, dates, CSVs, the Leak Scan).

## The contract

```python
"""<Statement Format> Parser."""   # one line; no client details anywhere in the file
import re
from datetime import datetime

from harness import MultipleAccounts            # raise it if the statement covers several accounts
from harness.money import amount, balance       # amount("1,234.56") -> Decimal; balance("12.00 CR", ACCOUNT_TYPE)

ISSUER = "Example Bank"                         # bank or card provider
STATEMENT_FORMAT = "Example Bank everyday"      # unique name for this layout
ACCOUNT_TYPE = "deposit"                        # "deposit" or "credit_card"
SIGNATURE = ["EXAMPLE BANK", "Everyday Account Statement"]  # printed text that identifies the layout
COLUMNS = ["Debits", "Credits"]                 # optional: see "Empty columns" below


def parse(text):
    ...
    return {
        "statement_period": (start_date, end_date),          # datetime.date
        "identifiers": {"account_number": "...", "bsb": "...", "holder_name": "...", "address": ["..."]},
        "opening_balance": balance(printed_opening, ACCOUNT_TYPE),
        "closing_balance": balance(printed_closing, ACCOUNT_TYPE),
        "transactions": [
            {"date": date_or_day_month, "description": "...", "amount": signed_amount},  # optional "fx": "..."
        ],
    }
```

- **Money In positive, Money Out negative**, on every account type: a purchase on a credit card is negative, a payment to the card positive.
- **Balances** are in the account's own direction: funds held for a deposit account, the amount owed for a credit card. Always read them with `balance()`, which handles CR/DR suffixes and minus signs.
- **Dates:** a `datetime.date`, or a `(day, month)` pair when the statement prints no year. The harness takes the year from the statement period. Put transactions in printed order; the harness sorts by date.
- **Descriptions:** the printed text, joined into one line if it wraps. Foreign-currency detail lines go in `"fx"` on the transaction above, verbatim, never as rows of their own.
- **Split tables** (debits and credits printed separately): read both, setting each row's sign by its table.
- **Empty columns:** if a row prints its amount in a Debits or Credits column and leaves the other empty, the text loses which column it was in. Set `COLUMNS` to the column headings exactly as printed (e.g. `["Withdrawals ($)", "Deposits ($)"]`): each amount under one of them then arrives tagged, as in `Credits:17,811.09`, and the Parser reads the sign from the tag. Never infer signs from widths, dot leaders or by making the balances add up.
- **Identifiers** are read from the statement each time; the harness uses them for file names and the Leak Scan. Never write them into the file.

## Never in a Parser

The Parser is saved to the firm's library, so nothing from the statement may be in it. The Leak Scan rejects any Parser containing the client's account number, BSB, name or address, or any of the statement's transaction descriptions or amounts. Anchor on what the bank prints for everyone: its name, headings, column titles, labels like "Opening balance". No example rows, no sample values, no comments quoting the statement, and no special cases for particular transactions or merchants.

## Reading the pages

Statement text comes from `harness pages`. Columns usually arrive as one line per row with single spaces, and amounts often carry CR/DR. Write regular expressions against the lines you see, allowing for wrapped descriptions and page headers or footers that repeat on every page. Skip lines that are neither balances nor rows.
