"""The Leak Scan: checks that a Parser's source contains none of the account-identifying details of the
statement it was built from. Reports only which kinds of detail leaked, never the values."""
import re

MIN_DIGIT_RUN = 6
NAME_STOPWORDS = {"PTY", "LTD", "LIMITED", "TRUST", "THE", "AND", "MR", "MRS", "MS", "DR"}
KINDS = [("account_number", "account number"), ("bsb", "BSB"), ("holder_name", "holder name"), ("address", "address")]


def _digits_leak(value, source_digits):
    digits = re.sub(r"\D", "", value)
    return any(digits[i:i + MIN_DIGIT_RUN] in source_digits for i in range(len(digits) - MIN_DIGIT_RUN + 1))


def _words_leak(value, source):
    words = [w for w in re.findall(r"[A-Za-z]{4,}", value) if w.upper() not in NAME_STOPWORDS]
    return value.upper() in source or any(re.search(rf"\b{re.escape(w.upper())}\b", source) for w in words)


def leaked_kinds(source, identifiers):
    upper = source.upper()
    # Digits with separators removed, so "1234 5678" in source still matches account 12345678.
    source_digits = re.sub(r"(?<=\d)[\s-]+(?=\d)", "", source)
    leaked = []
    for key, label in KINDS:
        values = identifiers.get(key) or []
        values = values if isinstance(values, list) else [values]
        if key in ("account_number", "bsb"):
            hit = any(_digits_leak(v, source_digits) for v in values)
        else:
            hit = any(_words_leak(v, upper) for v in values)
        if hit:
            leaked.append(label)
    return leaked


def contains_long_number(source):
    """The check available without a statement (at Promotion): any run of MIN_DIGIT_RUN or more digits, ignoring
    spaces and hyphens between them, looks like an account number."""
    digits = re.sub(r"(?<=\d)[\s-]+(?=\d)", "", source)
    return bool(re.search(rf"\d{{{MIN_DIGIT_RUN},}}", digits))


def transaction_kinds(source, transactions):
    """Statement lines quoted in a Parser (as examples, comments or special cases) would be saved to the firm's
    library with it. Short or one-word descriptions ("FEE", "WITHDRAWAL") are left alone: Parsers match on those."""
    upper = source.upper()
    leaked = []
    if any(len(d) >= 12 and len(d.split()) >= 2 and d.upper() in upper
           for d in (t["description"].strip() for t in transactions)):
        leaked.append("a transaction description")
    # Printed with or without thousands separators; zero is left alone, as Parsers may test for "0.00".
    printed = {f for t in transactions if t["amount"] for f in (f"{abs(t['amount']):,.2f}", f"{abs(t['amount']):.2f}")}
    if any(re.search(rf"(?<![\d.,]){re.escape(p)}(?!\d)", source) for p in printed):
        leaked.append("a transaction amount")
    return leaked
