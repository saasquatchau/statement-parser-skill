"""A Parser that declares COLUMNS gets each amount printed under one of those headings tagged with it, so it can
read statements that leave the unused debit or credit column empty."""
import subprocess
import sys

from tests.helpers import ROOT, run_harness
from tests.pdfs import make_table_pdf

COLUMNS_PARSERS = ROOT / "tests" / "parsers_columns"

# Headings are printed left-aligned over their columns; amounts are right-aligned to each column's edge.
ROWS = [
    [(40, "PROBE BANK", "left")],
    [(40, "Columns Account Statement", "left")],
    [(40, "Statement period 01/03/2026 to 31/03/2026", "left")],
    [(40, "Account number 062-000 1234 5678", "left")],
    [(40, "Opening balance 1,000.00", "left")],
    [(40, "Date", "left"), (110, "Details", "left"), (300, "Debits", "left"), (380, "Credits", "left"),
     (460, "Balance", "left")],
    [(40, "03/03/2026", "left"), (110, "SALARY ACME PTY LTD", "left"), (415, "2,500.00", "right"),
     (495, "3,500.00", "right")],
    [(40, "05/03/2026", "left"), (110, "WOOLWORTHS 1234 SYDNEY", "left"), (330, "84.20", "right"),
     (495, "3,415.80", "right")],
    [(40, "Closing balance 3,415.80", "left")],
]


def test_parser_declaring_columns_reads_amounts_by_the_column_they_sit_under(tmp_path):
    statement = make_table_pdf(tmp_path / "columns.pdf", ROWS)
    result = run_harness(statement, out=tmp_path / "out", parsers=[COLUMNS_PARSERS])

    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("PASS  columns.pdf: Probe Bank columns, 2 transactions, reconciled")


def harness(*args):
    return subprocess.run([sys.executable, "-m", "harness", *map(str, args)], cwd=ROOT, capture_output=True, text=True)


def test_build_pages_show_the_column_tags_a_parser_will_read(tmp_path):
    statement = make_table_pdf(tmp_path / "columns.pdf", ROWS)
    result = harness("pages", statement, "--columns", "Debits,Credits")

    assert "03/03/2026 SALARY ACME PTY LTD Credits:2,500.00 3,500.00" in result.stdout
    assert "05/03/2026 WOOLWORTHS 1234 SYDNEY Debits:84.20 3,415.80" in result.stdout


def test_build_check_judges_a_columns_parser_on_tagged_text(tmp_path):
    statement = make_table_pdf(tmp_path / "columns.pdf", ROWS)
    candidate = tmp_path / "probe_columns.py"
    candidate.write_text((COLUMNS_PARSERS / "probe_columns.py").read_text())
    result = harness("check", candidate, statement)

    assert result.stdout.splitlines()[0] == "ACCEPT probe_columns: reconciles 1 statement, Leak Scan passed"
