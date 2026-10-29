import argparse
import json
import re
from pathlib import Path

from harness import MultipleAccounts
from harness.build import check
from harness.dates import full_date, outside
from harness.extract import parser_text, statement_pages, statement_text
from harness.firm import bundled_ids, firm_config, is_artifact_link, write_firm_skill
from harness.leak import contains_long_number, leaked_kinds, transaction_kinds
from harness.output import duplicate_warning, group, write_csv
from harness.parsers import load_parser, load_parsers, matching


def reconciliation_gap(result, account_type):
    # Money In is positive. Deposit: closing = opening + Σ amounts. Credit card (balance owed): closing = opening − Σ amounts.
    total = sum(t["amount"] for t in result["transactions"])
    expected = result["opening_balance"] + (total if account_type == "deposit" else -total)
    return abs(result["closing_balance"] - expected)


def plural(count, noun):
    return f"{count} {noun}{'' if count == 1 else 's'}"


def report(status, name, detail):
    print(f"{status:<5} {name}: {detail}")


def apply(parser, text):
    """Runs one Parser; returns (result, None) on success or (None, failure reason)."""
    try:
        result = parser.parse(text)
        period = result["statement_period"]
        for t in result["transactions"]:
            t["date"] = full_date(t["date"], period)
        # Date order, keeping the printed order within a date (merges split debit and credit tables).
        result["transactions"].sort(key=lambda t: t["date"])
        gap = reconciliation_gap(result, parser.ACCOUNT_TYPE)
    except MultipleAccounts:
        return None, "multi-account statement, not supported"
    except Exception as e:
        # Report only the error type: Parser messages and tracebacks can quote statement content.
        return None, f"Parser error ({type(e).__name__})"
    if gap:
        return None, f"Reconciliation off by {gap:.2f}"
    # The account number names the CSV and keeps accounts apart; without it, accounts would merge.
    if len(re.sub(r"\D", "", str(result.get("identifiers", {}).get("account_number") or ""))) < 4:
        return None, "Parser didn't find the account number"
    return result, None


def pass_detail(parser, result, scanned):
    transactions = result["transactions"]
    detail = f"{parser.STATEMENT_FORMAT}, {plural(len(transactions), 'transaction')}, reconciled"
    stray = [t["date"] for t in transactions if outside(t["date"], result["statement_period"])]
    if stray:
        dates = ", ".join(d.strftime("%d/%m/%Y") for d in stray)
        detail += f"; {len(stray)} transaction{'s' if len(stray) > 1 else ''} dated outside the statement period ({dates})"
    if scanned:
        detail += "; scanned (OCR): check balances against the PDF"
    return detail


def run_statement(statement, sources, statement_format):
    """Tries each Parser source in precedence order (Bundled before Firm); `sources` is a list of
    (parsers, is_firm). Returns (parser, result, is_firm) if one reconciled, otherwise None."""
    try:
        text, scanned = statement_text(statement)
    except Exception as e:
        report("FAIL", statement.name, f"could not read statement ({type(e).__name__})")
        return None
    failure = None
    for parsers, is_firm in sources:
        candidates = matching(parsers, text, statement_format)
        if len(candidates) > 1:
            report("ASK", statement.name, "matches " + " | ".join(p.STATEMENT_FORMAT for p in candidates))
            return None
        if not candidates:
            continue
        parser = candidates[0]
        result, reason = apply(parser, parser_text(statement, parser, text))
        if result is not None:
            report("PASS", statement.name, pass_detail(parser, result, scanned))
            return parser, result, is_firm
        failure = failure or f"{parser.STATEMENT_FORMAT}, {reason}"
    if failure:
        report("FAIL", statement.name, failure)
    else:
        report("BUILD", statement.name, "no Parser matches")
    return None


def promotion_tip(outcomes):
    firm = [parser for parser, _, is_firm in outcomes if is_firm]
    if not firm:
        return None
    formats = list(dict.fromkeys(p.STATEMENT_FORMAT for p in firm))
    statements = f"{len(firm)} statement{'s' if len(firm) > 1 else ''}"
    used = f"used {'a Firm Parser' if len(formats) == 1 else 'Firm Parsers'} ({', '.join(formats)})"
    it = "it" if len(formats) == 1 else "them"
    return (f"{statements} {used}. Ask to \"promote our parsers\" to bundle {it} into the Firm Skill and skip fetching "
            f"{it} from the library each time.")


def run(args):
    sources = [(load_parsers(d), False) for d in args.parsers]
    sources += [(load_parsers(d), True) for d in args.firm_parsers or []]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    outcomes = [run_statement(s, sources, args.format) for s in map(Path, args.statements)]
    reconciled = [o for o in outcomes if o]
    for name, statements in group([(p, r) for p, r, _ in reconciled], args.per_statement).items():
        rows = write_csv(out / name, statements)
        count = len(statements)
        report("CSV", name, f"{plural(count, 'statement')}, {plural(len(rows), 'transaction')}")
        if warning := duplicate_warning(rows):
            report("WARN", name, warning)
    if tip := promotion_tip(reconciled):
        print(f"TIP   {tip}")
    unreconciled = len(outcomes) - len(reconciled)
    firm = firm_config()
    if unreconciled and firm and not args.firm_parsers:
        # Said here, at the moment it matters, rather than left to the skill to remember.
        statements = f"{unreconciled} statement{'s' if unreconciled > 1 else ''}"
        print(f"NEXT  {statements} may have a Firm Parser: follow \"Firm Parsers\" in SKILL.md (library {firm['library']})")
    return 0 if len(reconciled) == len(outcomes) else 1


def detect(args):
    """Matches library Signatures against sealed statements, so the skill fetches only the Firm Parsers it needs."""
    # Parsers this skill already bundles (promoted ones) are never fetched again.
    bundled = bundled_ids()
    library = [e for e in json.loads(Path(args.signatures).read_text()) if e["id"] not in bundled]
    for statement in map(Path, args.statements):
        try:
            text, _ = statement_text(statement)
        except Exception as e:
            report("FAIL", statement.name, f"could not read statement ({type(e).__name__})")
            continue
        found = [e for e in library if all(s in text for s in e["signature"])]
        if found:
            report("FETCH", statement.name, ", ".join(f"{e['id']} ({e['statement_format']})" for e in found))
        else:
            report("NONE", statement.name, "nothing to fetch from the library")
    return 0


def leak_scan(args):
    parser_path = Path(args.parser)
    parser = load_parser(parser_path)
    try:
        result = parser.parse(statement_text(args.statement, getattr(parser, "COLUMNS", ()))[0])
    except Exception as e:
        report("FAIL", parser_path.name, f"could not read identifying details ({type(e).__name__})")
        return 1
    source = parser_path.read_text()
    leaked = leaked_kinds(source, result["identifiers"]) + transaction_kinds(source, result["transactions"])
    if leaked:
        report("FAIL", parser_path.name, f"{', '.join(leaked)} found in Parser source")
        return 1
    report("PASS", parser_path.name, "no identifying details found")
    return 0


def pages(args):
    """Prints only the pages a Build needs: by default the first and last, where balances and headings usually are."""
    columns = args.columns.split(",") if args.columns else ()
    texts, scanned = statement_pages(args.statement, columns)
    wanted = sorted({1, len(texts)}) if not args.pages else [int(p) for p in args.pages.split(",")]
    for number in wanted:
        print(f"PAGE {number} of {len(texts)}{' (scanned, OCR)' if scanned else ''}")
        print(texts[number - 1])
    return 0


def build_check(args):
    return check(args.candidate, args.statements, args.signatures, apply, report)


def firm_skill(args):
    """Setup (with --firm and --library) or Promotion (with --promote, reading the rest from firm.json)."""
    config = firm_config() or {}
    firm, library = args.firm or config.get("firm"), args.library or config.get("library")
    if not firm or not library:
        report("FAIL", "firm-skill", "this skill hasn't been set up: pass --firm and --library")
        return 1
    if not is_artifact_link(library):
        report("FAIL", "firm-skill", "library must be a claude.ai artifact link (https://claude.ai/artifact/...)")
        return 1
    for parser in sorted(Path(args.promote).glob("*.py")) if args.promote else []:
        if contains_long_number(parser.read_text()):
            report("REJECT", parser.stem, "Leak Scan found a long number in the Parser; nothing was promoted")
            return 1
    version = config.get("version", 1) + 1 if config else 1
    archive, bundled, promoted = write_firm_skill(Path(args.out), firm, library, version, args.promote)
    report("SKILL", archive.name, f"Firm Skill v{version} for {firm}, {bundled} Bundled Parser{'s' if bundled != 1 else ''}")
    if promoted:
        print(f"PROMOTED {', '.join(promoted)}: set promoted_in to \"v{version}\" on their library rows")
    return 0


def main(argv):
    cli = argparse.ArgumentParser(prog="harness")
    commands = cli.add_subparsers(dest="command", required=True)
    run_cmd = commands.add_parser("run", help="Run Parsers over statements and write Xero CSVs")
    run_cmd.add_argument("statements", nargs="+")
    run_cmd.add_argument("--parsers", action="append", required=True, help="Parser source; repeat in precedence order")
    run_cmd.add_argument("--firm-parsers", action="append", help="Firm Parsers fetched from the library; tried last")
    run_cmd.add_argument("--out", required=True)
    run_cmd.add_argument("--per-statement", action="store_true", help="One CSV per statement instead of per account")
    run_cmd.add_argument("--format", help="Use the Parser for this Statement Format, skipping Signature detection")
    scan_cmd = commands.add_parser("leak-scan", help="Check a Parser contains no identifying details from a statement")
    scan_cmd.add_argument("parser")
    scan_cmd.add_argument("statement")
    detect_cmd = commands.add_parser("detect", help="Name the library Parsers whose Signatures match each statement")
    detect_cmd.add_argument("statements", nargs="+")
    detect_cmd.add_argument("--signatures", required=True, help="JSON list of {id, statement_format, signature}")
    pages_cmd = commands.add_parser("pages", help="Print statement pages for a Build (the only step that reads content)")
    pages_cmd.add_argument("statement")
    pages_cmd.add_argument("--pages", help="Comma-separated page numbers; default first and last")
    pages_cmd.add_argument("--columns", help="Comma-separated column headings to tag amounts with (a Parser's COLUMNS)")
    check_cmd = commands.add_parser("check", help="Accept or reject a candidate Parser written during a Build")
    check_cmd.add_argument("candidate")
    check_cmd.add_argument("statements", nargs="+")
    check_cmd.add_argument("--signatures", help="JSON list of the library's {id, statement_format, signature}")
    firm_cmd = commands.add_parser("firm-skill", help="Rebuild this skill as a Firm Skill carrying the firm's library")
    firm_cmd.add_argument("--library", help="Address of the firm's library artifact (Setup)")
    firm_cmd.add_argument("--firm", help="The firm's name (Setup)")
    firm_cmd.add_argument("--promote", help="Folder of Firm Parsers to bundle into the Firm Skill (Promotion)")
    firm_cmd.add_argument("--out", required=True)
    args = cli.parse_args(argv)
    handlers = {"run": run, "detect": detect, "pages": pages, "check": build_check, "leak-scan": leak_scan,
                "firm-skill": firm_skill}
    return handlers[args.command](args)
