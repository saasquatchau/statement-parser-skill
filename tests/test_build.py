import json
import shutil
import subprocess
import sys

from tests.helpers import FIXTURES, PARSERS, ROOT

FIRM = ROOT / "tests" / "parsers_firm"
CANDIDATE = FIRM / "probe_bank_deposit_2027.py"
REDESIGNED = FIXTURES / "probe-deposit-2027-layout.txt"


def harness(*args):
    return subprocess.run([sys.executable, "-m", "harness", *map(str, args)], cwd=ROOT, capture_output=True, text=True)


def candidate_copy(source, tmp_path, name=None):
    """Builds write their candidate to a scratch folder; attempts are counted beside it."""
    path = tmp_path / (name or source.name)
    shutil.copy(source, path)
    return path


def test_pages_prints_the_first_and_last_page_by_default():
    result = harness("pages", REDESIGNED)

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "PAGE 1 of 1"
    assert "Opening balance 1,000.00" in result.stdout


def test_candidate_that_reconciles_every_statement_of_its_format_is_accepted(tmp_path):
    candidate = candidate_copy(CANDIDATE, tmp_path)
    result = harness("check", candidate, REDESIGNED)

    assert result.returncode == 0, result.stdout
    lines = result.stdout.splitlines()
    assert lines[0] == "ACCEPT probe_bank_deposit_2027: reconciles 1 statement, Leak Scan passed"
    assert lines[1].startswith("ROW   ")
    assert json.loads(lines[1][6:]) == {
        "id": "probe_bank_deposit_2027", "statement_format": "Probe Bank deposit 2027 layout", "issuer": "Probe Bank",
        "account_type": "deposit", "signature": ["PROBE BANK", "Everyday Account Statement"],
    }


def test_candidate_must_reconcile_all_matching_statements_in_the_batch(tmp_path):
    candidate = candidate_copy(PARSERS / "probe_bank_deposit.py", tmp_path)
    result = harness("check", candidate, FIXTURES / "probe-deposit-march.txt", FIXTURES / "probe-deposit-april.txt",
                     FIXTURES / "unknown-bank.txt")

    assert result.stdout.splitlines()[0] == "ACCEPT probe_bank_deposit: reconciles 2 statements, Leak Scan passed"


def test_candidate_that_does_not_reconcile_is_rejected_with_its_attempt_count(tmp_path):
    candidate = candidate_copy(ROOT / "tests" / "parsers_wrong_field" / "probe_card_wrong_field.py", tmp_path)
    result = harness("check", candidate, FIXTURES / "probe-card-march.txt")

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "REJECT probe_card_wrong_field: probe-card-march.txt Reconciliation off by 8909.00 (attempt 1 of 3)",
    ]


def test_third_failed_attempt_says_to_stop(tmp_path):
    candidate = candidate_copy(ROOT / "tests" / "parsers_wrong_field" / "probe_card_wrong_field.py", tmp_path)
    for _ in range(2):
        harness("check", candidate, FIXTURES / "probe-card-march.txt")
    result = harness("check", candidate, FIXTURES / "probe-card-march.txt")

    assert result.stdout.splitlines()[-1].endswith("(attempt 3 of 3: stop and report to the bookkeeper)")


def test_leaky_candidate_is_rejected_without_repeating_the_details(tmp_path):
    candidate = candidate_copy(ROOT / "tests" / "parsers_leaky" / "probe_bank_leaky.py", tmp_path)
    result = harness("check", candidate, FIXTURES / "probe-deposit-march.txt")

    assert result.stdout.splitlines() == [
        "REJECT probe_bank_leaky: Leak Scan found account number, holder name in the Parser (attempt 1 of 3)",
    ]


def test_candidate_quoting_a_transaction_description_is_rejected_without_repeating_it(tmp_path):
    candidate = tmp_path / "probe_bank_deposit.py"
    source = (PARSERS / "probe_bank_deposit.py").read_text()
    candidate.write_text(source + "\n# e.g. TRANSFER TO SAVINGS\n")
    result = harness("check", candidate, FIXTURES / "probe-deposit-march.txt")

    assert result.stdout.splitlines() == [
        "REJECT probe_bank_deposit: Leak Scan found a transaction description in the Parser (attempt 1 of 3)",
    ]


def test_candidate_quoting_a_transaction_amount_is_rejected_without_repeating_it(tmp_path):
    candidate = tmp_path / "probe_bank_deposit.py"
    source = (PARSERS / "probe_bank_deposit.py").read_text()
    candidate.write_text(source + "\n# the salary row is 2,500.00\n")
    result = harness("check", candidate, FIXTURES / "probe-deposit-march.txt")

    assert result.stdout.splitlines() == [
        "REJECT probe_bank_deposit: Leak Scan found a transaction amount in the Parser (attempt 1 of 3)",
    ]


def test_candidate_whose_signature_misses_the_statement_is_rejected(tmp_path):
    candidate = candidate_copy(CANDIDATE, tmp_path)
    result = harness("check", candidate, FIXTURES / "unknown-bank.txt")

    assert result.stdout.splitlines() == [
        "REJECT probe_bank_deposit_2027: Signature matches none of the statements (attempt 1 of 3)",
    ]


def test_candidate_breaking_the_parser_contract_is_rejected(tmp_path):
    candidate = candidate_copy(ROOT / "tests" / "parsers_bad_contract" / "no_issuer.py", tmp_path)
    result = harness("check", candidate, REDESIGNED)

    assert result.stdout.splitlines() == ["REJECT no_issuer: Parser contract: missing ISSUER (attempt 1 of 3)"]


def test_existing_library_parser_wins_over_a_new_build(tmp_path):
    candidate = candidate_copy(CANDIDATE, tmp_path, "probe_bank_2027_again.py")
    result = harness("check", candidate, REDESIGNED, "--signatures", FIXTURES / "library-signatures.json")

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "EXISTS probe-deposit-2027-layout.txt: probe_bank_deposit_2027 (Probe Bank deposit 2027 layout) is already "
        "in the library; fetch and use it instead of saving this Build",
    ]
