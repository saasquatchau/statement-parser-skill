import pytest

from tests.helpers import FIXTURES, ROOT, only_csv, run_harness


@pytest.mark.parametrize("fixture, rows", [
    ("probe-card-march.txt", 3),         # owed balance, payment and purchases
    ("probe-card-in-credit.txt", 2),     # overpaid card: balances printed with CR
    ("probe-card-minus-sign.txt", 1),    # card in credit shown with a minus sign, crossing to owed
    ("probe-deposit-overdrawn.txt", 2),  # overdrawn deposit account: balances printed with DR
])
def test_balances_reconcile_in_the_account_types_direction(tmp_path, fixture, rows):
    result = run_harness(FIXTURES / fixture, out=tmp_path)

    assert result.returncode == 0, result.stdout
    noun = "transaction" if rows == 1 else "transactions"
    assert result.stdout.splitlines()[0].endswith(f", {rows} {noun}, reconciled")


def test_credit_card_csv_keeps_money_in_positive(tmp_path):
    run_harness(FIXTURES / "probe-card-march.txt", out=tmp_path)

    assert only_csv(tmp_path).splitlines()[1:] == [
        "02/03/2026,1200.00,,PAYMENT THANK YOU,",
        "10/03/2026,-450.00,,QANTAS AIRWAYS,",
        "22/03/2026,-95.50,,COLES 0456,",
    ]


def test_parser_reading_the_wrong_balance_field_fails_reconciliation(tmp_path):
    result = run_harness(FIXTURES / "probe-card-march.txt", out=tmp_path, parsers=[ROOT / "tests" / "parsers_wrong_field"])

    assert result.returncode != 0
    assert result.stdout.startswith("FAIL  probe-card-march.txt: Probe Card (wrong field), Reconciliation off by ")
