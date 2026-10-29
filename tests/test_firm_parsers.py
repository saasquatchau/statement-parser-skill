import subprocess
import sys

from tests.helpers import FIXTURES, PARSERS, ROOT, run_harness

FIRM = ROOT / "tests" / "parsers_firm"
SIGNATURES = FIXTURES / "library-signatures.json"


def detect(*statements):
    return subprocess.run(
        [sys.executable, "-m", "harness", "detect", *map(str, statements), "--signatures", str(SIGNATURES)],
        cwd=ROOT, capture_output=True, text=True,
    )


def test_detect_names_the_library_parsers_to_fetch_for_each_statement():
    result = detect(FIXTURES / "probe-deposit-2027-layout.txt", FIXTURES / "unknown-bank.txt")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "FETCH probe-deposit-2027-layout.txt: probe_bank_deposit_2027 (Probe Bank deposit 2027 layout)",
        "NONE  unknown-bank.txt: nothing to fetch from the library",
    ]


def test_run_falls_back_to_firm_parsers_and_suggests_promotion(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-2027-layout.txt", out=tmp_path, options=["--firm-parsers", str(FIRM)])

    assert result.returncode == 0, result.stdout
    lines = result.stdout.splitlines()
    assert lines[0].startswith("PASS  probe-deposit-2027-layout.txt: Probe Bank deposit 2027 layout,")
    assert lines[-1] == (
        "TIP   1 statement used a Firm Parser (Probe Bank deposit 2027 layout). "
        "Ask to \"promote our parsers\" to bundle it into the Firm Skill and skip fetching it from the library each time."
    )


def test_no_promotion_suggestion_when_only_bundled_parsers_were_used(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path, options=["--firm-parsers", str(FIRM)])

    assert result.returncode == 0, result.stdout
    assert not [line for line in result.stdout.splitlines() if line.startswith("TIP")]
