"""Every Curated Parser reconciles its synthetic fixture (tests/fixtures/curated/<parser id>.txt) and passes the
Leak Scan against it. Fixtures are written by hand to the Statement Format's layout, with made-up details and
transactions; fixtures redacted from real statements stay in private/ (see tests/test_private_fixtures.py)."""
import subprocess
import sys

import pytest

from tests.helpers import ROOT, run_harness

CURATED = ROOT / "parsers" / "curated"
FIXTURES = ROOT / "tests" / "fixtures" / "curated"
EXPECTED = {
    "amex_credit_card": ("American Express credit card", 3),
    "amex_credit_card_2020": ("American Express credit card (2020 layout)", 3),
    "anz_business_advantage": ("ANZ Business Advantage statement", 3),
    "anz_business_classic_overdraft": ("ANZ Business Classic with Business Overdraft statement", 3),
    "anz_business_essentials": ("ANZ Business Essentials", 3),
    "anz_business_one_card": ("ANZ Business One credit card statement", 3),
    "cba_business_transaction": ("CommBank Business Transaction Account", 4),
    "ing_orange_everyday": ("ING Orange Everyday", 3),
    "macquarie_savings": ("Macquarie Savings Account", 3),
    "nab_business_everyday": ("NAB Business Everyday Account statement", 4),
    "westpac_choice": ("Westpac Choice electronic statement", 3),
}


def test_every_curated_parser_has_a_fixture():
    assert sorted(p.stem for p in CURATED.glob("*.py")) == sorted(p.stem for p in FIXTURES.glob("*.txt"))


@pytest.mark.parametrize("parser_id", sorted(EXPECTED))
def test_curated_parser_reconciles_its_fixture(tmp_path, parser_id):
    statement_format, transactions = EXPECTED[parser_id]
    result = run_harness(FIXTURES / f"{parser_id}.txt", out=tmp_path, parsers=[CURATED])

    assert result.returncode == 0, result.stdout
    noun = "transaction" if transactions == 1 else "transactions"
    assert result.stdout.startswith(f"PASS  {parser_id}.txt: {statement_format}, {transactions} {noun}, reconciled")


@pytest.mark.parametrize("parser_id", sorted(EXPECTED))
def test_curated_parser_passes_the_leak_scan(parser_id):
    result = subprocess.run([sys.executable, "-m", "harness", "leak-scan", str(CURATED / f"{parser_id}.py"),
                             str(FIXTURES / f"{parser_id}.txt")], cwd=ROOT, capture_output=True, text=True)

    assert result.returncode == 0, result.stdout
