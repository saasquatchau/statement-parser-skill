from tests.helpers import FIXTURES, run_harness

MARCH = FIXTURES / "probe-deposit-march.txt"
APRIL = FIXTURES / "probe-deposit-april.txt"


def test_batch_for_one_account_becomes_one_combined_csv_named_for_xero(tmp_path):
    result = run_harness(APRIL, MARCH, out=tmp_path)

    assert result.returncode == 0, result.stdout
    assert [p.name for p in tmp_path.iterdir()] == ["Probe-Bank-DEP-xx5678-2026-03-to-2026-04.csv"]
    assert (tmp_path / "Probe-Bank-DEP-xx5678-2026-03-to-2026-04.csv").read_text() == (
        "*Date,*Amount,Payee,Description,Reference\n"
        "03/03/2026,2500.00,,SALARY ACME PTY LTD,\n"
        "05/03/2026,-84.20,,WOOLWORTHS 1234 SYDNEY,\n"
        "17/03/2026,-500.00,,TRANSFER TO SAVINGS,\n"
        "02/04/2026,2500.00,,SALARY ACME PTY LTD,\n"
        "09/04/2026,-61.35,,WOOLWORTHS 1234 SYDNEY,\n"
    )
    assert result.stdout.splitlines()[-1] == "CSV   Probe-Bank-DEP-xx5678-2026-03-to-2026-04.csv: 2 statements, 5 transactions"


def test_per_statement_option_writes_one_csv_per_statement(tmp_path):
    result = run_harness(MARCH, APRIL, out=tmp_path, options=["--per-statement"])

    assert result.returncode == 0, result.stdout
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "Probe-Bank-DEP-xx5678-2026-03.csv",
        "Probe-Bank-DEP-xx5678-2026-04.csv",
    ]


def test_failed_statement_is_left_out_of_the_combined_csv_and_listed(tmp_path):
    result = run_harness(MARCH, FIXTURES / "probe-deposit-unreconciled.txt", out=tmp_path)

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "PASS  probe-deposit-march.txt: Probe Bank deposit, 3 transactions, reconciled",
        "FAIL  probe-deposit-unreconciled.txt: Probe Bank deposit, Reconciliation off by 12.40",
        "CSV   Probe-Bank-DEP-xx5678-2026-03.csv: 1 statement, 3 transactions",
    ]


def test_identical_rows_are_flagged_by_row_date_and_amount_without_removing_them(tmp_path):
    result = run_harness(MARCH, MARCH, out=tmp_path)

    lines = (tmp_path / "Probe-Bank-DEP-xx5678-2026-03.csv").read_text().splitlines()
    assert len(lines) == 7
    assert result.stdout.splitlines()[-1] == (
        "WARN  Probe-Bank-DEP-xx5678-2026-03.csv: 3 sets of identical rows "
        "(rows 2/3 03/03/2026 2500.00; rows 4/5 05/03/2026 -84.20; rows 6/7 17/03/2026 -500.00). Check before importing."
    )


def test_a_single_set_of_identical_rows_is_named_in_the_singular(tmp_path):
    statement = tmp_path / "probe-deposit-one-repeat.txt"
    lines = (FIXTURES / "probe-deposit-march.txt").read_text().splitlines()
    repeat = "05/03/2026 WOOLWORTHS 1234 SYDNEY 84.20 DR"
    lines.insert(lines.index(repeat), repeat)
    lines[-1] = "Closing balance 2,831.60"
    statement.write_text("\n".join(lines) + "\n")
    result = run_harness(statement, out=tmp_path / "out")

    assert "1 set of identical rows (rows 3/4 05/03/2026 -84.20)" in result.stdout.splitlines()[-1]


def test_duplicate_warning_lists_at_most_five_sets(tmp_path):
    may = FIXTURES / "probe-deposit-may.txt"
    result = run_harness(MARCH, MARCH, APRIL, APRIL, may, may, out=tmp_path)

    warning = result.stdout.splitlines()[-1]
    assert warning.startswith("WARN  Probe-Bank-DEP-xx5678-2026-03-to-2026-05.csv: 6 sets of identical rows (")
    listed = warning[warning.index("(") + 1:warning.index(")")].split("; ")
    assert len([item for item in listed if item.startswith("rows ")]) == 5
    assert "; +1 more). Check before importing." in warning
    assert "WOOLWORTHS" not in result.stdout and "SALARY" not in result.stdout
