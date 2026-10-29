from tests.helpers import FIXTURES, only_csv, run_harness


def test_dates_without_a_year_take_it_from_the_statement_period(tmp_path):
    result = run_harness(FIXTURES / "probe-store-card-dec-jan.txt", out=tmp_path)

    assert result.returncode == 0, result.stdout
    assert only_csv(tmp_path).splitlines()[1:] == [
        "28/12/2025,-120.00,,MYER CITY,",
        "03/01/2026,20.00,,MYER CITY REFUND,",
    ]


def test_transaction_dated_outside_the_statement_period_is_flagged(tmp_path):
    result = run_harness(FIXTURES / "probe-store-card-out-of-period.txt", out=tmp_path)

    assert result.stdout.splitlines()[:1] == [
        "PASS  probe-store-card-out-of-period.txt: Probe Store Card, 2 transactions, reconciled; "
        "1 transaction dated outside the statement period (20/03/2026)",
    ]


def test_charge_dated_a_few_days_before_the_period_is_not_flagged(tmp_path):
    # Card issuers often list charges made a day or two before the period starts; only dates more than 31 days
    # outside the period (such as a year inferred wrongly) are worth a warning.
    result = run_harness(FIXTURES / "probe-store-card-early-charge.txt", out=tmp_path)

    assert result.stdout.splitlines()[0] == "PASS  probe-store-card-early-charge.txt: Probe Store Card, 2 transactions, reconciled"
