import shutil

import pytest

from tests.helpers import FIXTURES, run_harness
from tests.pdfs import scanned_pdf_from_fixture


@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract is not installed")
def test_scanned_statement_is_read_by_ocr_and_passes_with_a_warning(tmp_path):
    scanned = scanned_pdf_from_fixture(FIXTURES / "probe-deposit-march.txt", tmp_path / "in")
    result = run_harness(scanned, out=tmp_path / "out")

    assert result.returncode == 0, result.stdout
    assert result.stdout.splitlines()[0] == (
        "PASS  probe-deposit-march-scanned.pdf: Probe Bank deposit, 3 transactions, reconciled; "
        "scanned (OCR): check balances against the PDF"
    )


def test_statement_covering_several_accounts_is_rejected(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-two-accounts.txt", out=tmp_path)

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "FAIL  probe-deposit-two-accounts.txt: Probe Bank deposit, multi-account statement, not supported",
    ]
    assert list(tmp_path.iterdir()) == []
