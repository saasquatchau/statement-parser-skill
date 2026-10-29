from tests.helpers import FIXTURES, PARSERS, ROOT, run_harness

AMBIGUOUS = ROOT / "tests" / "parsers_ambiguous"
FIRM = ROOT / "tests" / "parsers_firm"


def test_statement_with_no_matching_signature_is_a_build_candidate(tmp_path):
    result = run_harness(FIXTURES / "unknown-bank.txt", out=tmp_path)

    assert result.returncode != 0
    assert result.stdout.splitlines() == ["BUILD unknown-bank.txt: no Parser matches"]
    assert list(tmp_path.iterdir()) == []


def test_ambiguous_signatures_name_the_candidates_for_the_bookkeeper(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path, parsers=[AMBIGUOUS])

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "ASK   probe-deposit-march.txt: matches Probe Bank deposit | Probe Bank everyday",
    ]


def test_named_statement_format_resolves_an_ambiguous_match(tmp_path):
    result = run_harness(
        FIXTURES / "probe-deposit-march.txt", out=tmp_path, parsers=[AMBIGUOUS],
        options=["--format", "Probe Bank everyday"],
    )

    assert result.returncode == 0
    assert result.stdout.startswith("PASS  probe-deposit-march.txt: Probe Bank everyday,")


def test_named_statement_format_cannot_force_a_parser_whose_signature_does_not_match(tmp_path):
    result = run_harness(FIXTURES / "unknown-bank.txt", out=tmp_path, options=["--format", "Probe Bank deposit"])

    assert result.returncode != 0
    assert result.stdout.splitlines() == ["BUILD unknown-bank.txt: no Parser matches"]


def test_bundled_parser_is_used_before_a_firm_parser(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-march.txt", out=tmp_path, parsers=[PARSERS, FIRM])

    assert result.stdout.startswith("PASS  probe-deposit-march.txt: Probe Bank deposit,")


def test_firm_parser_is_tried_when_the_bundled_parser_fails(tmp_path):
    result = run_harness(FIXTURES / "probe-deposit-2027-layout.txt", out=tmp_path, parsers=[PARSERS, FIRM])

    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("PASS  probe-deposit-2027-layout.txt: Probe Bank deposit 2027 layout,")
