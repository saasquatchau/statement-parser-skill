import subprocess
import sys

from tests.helpers import FIXTURES, PARSERS, ROOT

MARCH = FIXTURES / "probe-deposit-march.txt"


def leak_scan(parser, statement):
    return subprocess.run(
        [sys.executable, "-m", "harness", "leak-scan", str(parser), str(statement)],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_parser_using_only_issuer_text_passes(tmp_path):
    result = leak_scan(PARSERS / "probe_bank_deposit.py", MARCH)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == ["PASS  probe_bank_deposit.py: no identifying details found"]


def test_parser_containing_client_details_fails_without_repeating_them(tmp_path):
    result = leak_scan(ROOT / "tests" / "parsers_leaky" / "probe_bank_leaky.py", MARCH)

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "FAIL  probe_bank_leaky.py: account number, holder name found in Parser source",
    ]
    for value in ["CITIZEN", "Citizen", "1234", "5678"]:
        assert value not in result.stdout + result.stderr
