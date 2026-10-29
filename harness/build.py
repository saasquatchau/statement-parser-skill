"""Checks a candidate Parser written during a Build: it must follow the Parser contract, match and reconcile every
statement of its Statement Format in the batch, and pass the Leak Scan. Failed attempts are counted beside the
candidate so a Build stops after three."""
import json
import re
from pathlib import Path

from harness.extract import parser_text, statement_text
from harness.leak import leaked_kinds, transaction_kinds
from harness.parsers import load_parser

MAX_ATTEMPTS = 3
PARSER_ID = re.compile(r"^[a-z][a-z0-9_]*$")
ACCOUNT_TYPES = ("deposit", "credit_card")


def contract_problem(path, parser):
    if not PARSER_ID.match(path.stem):
        return "Parser id must be lowercase letters, digits and underscores"
    for name in ("ISSUER", "STATEMENT_FORMAT", "ACCOUNT_TYPE", "SIGNATURE", "parse"):
        if not hasattr(parser, name):
            return f"missing {name}"
    if parser.ACCOUNT_TYPE not in ACCOUNT_TYPES:
        return f"ACCOUNT_TYPE must be one of {', '.join(ACCOUNT_TYPES)}"
    if not parser.SIGNATURE or not all(isinstance(s, str) and s for s in parser.SIGNATURE):
        return "SIGNATURE must be a non-empty list of strings"
    return None


def record_failure(candidate):
    """Counts a failed attempt; returns the suffix for the REJECT line."""
    counter = candidate.with_suffix(".attempts")
    attempt = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(attempt))
    if attempt >= MAX_ATTEMPTS:
        return f"(attempt {attempt} of {MAX_ATTEMPTS}: stop and report to the bookkeeper)"
    return f"(attempt {attempt} of {MAX_ATTEMPTS})"


def library_row(parser, parser_id):
    return {"id": parser_id, "statement_format": parser.STATEMENT_FORMAT, "issuer": parser.ISSUER,
            "account_type": parser.ACCOUNT_TYPE, "signature": list(parser.SIGNATURE)}


def check(candidate, statements, signatures, apply, report):
    """`apply(parser, text)` is the Run's own parse-and-reconcile step, so a Build is judged exactly as Runs are.
    Returns the exit code."""
    candidate = Path(candidate)
    name = candidate.stem

    def reject(reason):
        report("REJECT", name, f"{reason} {record_failure(candidate)}")
        return 1

    try:
        parser = load_parser(candidate)
    except Exception as e:
        return reject(f"Parser does not load ({type(e).__name__})")
    if problem := contract_problem(candidate, parser):
        return reject(f"Parser contract: {problem}")

    texts = [(Path(s), statement_text(s)[0]) for s in statements]
    matched = [(s, t) for s, t in texts if all(sig in t for sig in parser.SIGNATURE)]
    if not matched:
        return reject("Signature matches none of the statements")

    if signatures:
        library = json.loads(Path(signatures).read_text())
        for statement, text in matched:
            for entry in library:
                if all(sig in text for sig in entry["signature"]):
                    report("EXISTS", statement.name, f"{entry['id']} ({entry['statement_format']}) is already in the "
                                                     "library; fetch and use it instead of saving this Build")
                    return 1

    identifiers, transactions = [], []
    for statement, text in matched:
        result, reason = apply(parser, parser_text(statement, parser, text))
        if result is None:
            return reject(f"{statement.name} {reason}")
        identifiers.append(result["identifiers"])
        transactions += result["transactions"]

    source = candidate.read_text()
    leaked = sorted({kind for ids in identifiers for kind in leaked_kinds(source, ids)},
                    key=["account number", "BSB", "holder name", "address"].index)
    leaked += transaction_kinds(source, transactions)
    if leaked:
        return reject(f"Leak Scan found {', '.join(leaked)} in the Parser")

    count = len(matched)
    report("ACCEPT", name, f"reconciles {count} statement{'s' if count > 1 else ''}, Leak Scan passed")
    print("ROW   " + json.dumps(library_row(parser, name)))
    return 0
