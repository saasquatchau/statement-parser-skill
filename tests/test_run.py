from tests.helpers import FIXTURES, only_csv, run_harness
from tests.pdfs import pdf_from_fixture


def test_reconciling_deposit_statement_becomes_a_xero_csv(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path)

    assert result.returncode == 0, result.stderr
    assert only_csv(tmp_path) == (
        "*Date,*Amount,Payee,Description,Reference\n"
        "03/03/2026,2500.00,,SALARY ACME PTY LTD,\n"
        "05/03/2026,-84.20,,WOOLWORTHS 1234 SYDNEY,\n"
        "17/03/2026,-500.00,,TRANSFER TO SAVINGS,\n"
    )
    assert result.stdout.splitlines() == [
        "PASS  probe-deposit-march.txt: Probe Bank deposit, 3 transactions, reconciled",
        "CSV   Probe-Bank-DEP-xx5678-2026-03.csv: 1 statement, 3 transactions",
    ]


def test_statement_that_does_not_reconcile_fails_without_a_csv(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-unreconciled.txt", out=tmp_path)

    assert result.returncode != 0
    assert list(tmp_path.iterdir()) == []
    assert result.stdout.splitlines() == [
        "FAIL  probe-deposit-unreconciled.txt: Probe Bank deposit, Reconciliation off by 12.40",
    ]


DESCRIPTIONS = ["SALARY ACME PTY LTD", "WOOLWORTHS 1234 SYDNEY", "TRANSFER TO SAVINGS"]


def test_parser_error_fails_the_statement_without_revealing_statement_content(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-bad-date.txt", out=tmp_path)

    assert result.returncode != 0
    assert list(tmp_path.iterdir()) == []
    assert result.stdout.splitlines() == [
        "FAIL  probe-deposit-bad-date.txt: Probe Bank deposit, Parser error (ValueError)",
    ]
    assert result.stderr == ""


def test_no_output_ever_contains_transaction_descriptions(tmp_path):
    outputs = [
        run_harness(FIXTURES / name, out=tmp_path)
        for name in ["probe-deposit-march.txt", "probe-deposit-unreconciled.txt", "probe-deposit-bad-date.txt"]
    ]

    assert [r.stdout[:4] for r in outputs] == ["PASS", "FAIL", "FAIL"]
    for result in outputs:
        for description in DESCRIPTIONS:
            assert description not in result.stdout + result.stderr


def test_pdf_statement_gives_the_same_result_as_its_text(tmp_path):
    pdf = pdf_from_fixture(FIXTURES / "probe-deposit-march.txt", tmp_path / "in")
    from_text = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path / "text")
    from_pdf = run_harness(pdf, out=tmp_path / "pdf")

    assert from_pdf.returncode == 0, from_pdf.stdout + from_pdf.stderr
    assert only_csv(tmp_path / "pdf") == only_csv(tmp_path / "text")
    assert from_pdf.stdout == from_text.stdout.replace(".txt", ".pdf")


def test_parser_that_misreads_the_account_number_fails_rather_than_merging_accounts(tmp_path):
    from tests.helpers import ROOT

    result = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path,
                         parsers=[ROOT / "tests" / "parsers_no_account"])

    assert result.returncode != 0
    assert result.stdout.splitlines()[0] == (
        "FAIL  probe-deposit-march.txt: Probe Bank (no account number), Parser didn't find the account number"
    )
