from tests.helpers import FIXTURES, only_csv, run_harness


def test_fx_detail_lines_are_appended_to_the_description_not_rows(tmp_path):
    result = run_harness(FIXTURES / "probe-express-fx.txt", out=tmp_path)

    assert result.returncode == 0, result.stdout
    assert only_csv(tmp_path).splitlines()[1:] == [
        "03/06/2026,-73.10,,AMAZON US SEATTLE 45.00 US Dollars Currency conversion rate 0.6156,",
        "21/06/2026,73.10,,PAYMENT RECEIVED THANK YOU,",
    ]


def test_split_debit_and_credit_tables_merge_into_date_order(tmp_path):
    result = run_harness(FIXTURES / "probe-split-card.txt", out=tmp_path)

    assert result.returncode == 0, result.stdout
    assert only_csv(tmp_path).splitlines()[1:] == [
        "05/07/2026,-50.00,,WOOLWORTHS,",
        "05/07/2026,-70.00,,BP FUEL,",
        "05/07/2026,10.00,,REFUND WOOLWORTHS,",
        "12/07/2026,500.00,,PAYMENT,",
        "20/07/2026,-200.00,,JB HIFI,",
    ]
