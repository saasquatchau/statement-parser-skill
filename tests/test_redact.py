import subprocess
import sys

from tests.helpers import FIXTURES, PARSERS, ROOT, run_harness


def redact(statement, parser, out):
    return subprocess.run([sys.executable, "scripts/redact.py", str(statement), str(parser), str(out)],
                          cwd=ROOT, capture_output=True, text=True)


def test_redacted_fixture_hides_identities_and_still_reconciles(tmp_path):
    out = tmp_path / "redacted.txt"
    result = redact(FIXTURES / "probe-deposit-march.txt", PARSERS / "probe_bank_deposit.py", out)

    assert result.returncode == 0, result.stderr
    text = out.read_text()
    for detail in ["JANE CITIZEN", "12 EXAMPLE STREET", "1234 5678"]:
        assert detail not in text
    assert "2,500.00" in text and "Closing balance 2,915.80" in text

    run = run_harness(out, out=tmp_path / "csv")
    assert run.returncode == 0, run.stdout
    assert run.stdout.splitlines()[0].endswith("3 transactions, reconciled")


def test_localities_and_postcodes_are_redacted_but_parser_labels_are_kept(tmp_path):
    out = tmp_path / "redacted.txt"
    result = subprocess.run(
        [sys.executable, "scripts/redact.py", str(FIXTURES / "probe-deposit-march.txt"),
         str(PARSERS / "probe_bank_deposit.py"), str(out), "--localities", str(FIXTURES / "localities-sample.txt")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = out.read_text()
    assert "WOOLWORTHS 1234 SUBURB" in text
    assert "SYDNEY" not in text and "NSW 2000" not in text
    # "Everyday Account Statement" is part of the Parser's Signature, so it must survive redaction.
    assert "Everyday Account Statement" in text


def test_extra_terms_named_by_the_reviewer_are_redacted(tmp_path):
    out = tmp_path / "redacted.txt"
    result = subprocess.run(
        [sys.executable, "scripts/redact.py", str(FIXTURES / "probe-deposit-march.txt"),
         str(PARSERS / "probe_bank_deposit.py"), str(out), "--also", "ACME", "--also", "SAVINGS"],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ACME" not in out.read_text() and "SAVINGS" not in out.read_text()


def test_first_names_are_redacted_but_parser_labels_are_kept(tmp_path):
    out = tmp_path / "redacted.txt"
    result = subprocess.run(
        [sys.executable, "scripts/redact.py", str(FIXTURES / "probe-deposit-march.txt"),
         str(PARSERS / "probe_bank_deposit.py"), str(out), "--names", str(FIXTURES / "names-redact-sample.txt")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = out.read_text()
    assert "SALARY NAME PTY LTD" in text
    assert "Everyday Account Statement" in text


def test_word_lists_skip_web_addresses_and_state_codes(tmp_path):
    statement = tmp_path / "statement.txt"
    statement.write_text((FIXTURES / "probe-deposit-march.txt").read_text().replace(
        "Everyday Account Statement", "Everyday Account Statement\nVisit probebank.com.au or help@probebank.com SYDNEY NSW 2000 VIC 3000"))
    out = tmp_path / "redacted.txt"
    result = subprocess.run(
        [sys.executable, "scripts/redact.py", str(statement), str(PARSERS / "probe_bank_deposit.py"), str(out),
         "--names", str(FIXTURES / "names-redact-sample.txt")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    text = out.read_text()
    assert "probebank.com.au" in text
    assert "VIC 0000" in text
