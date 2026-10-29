"""Curated Parsers against fixtures redacted from real statements. Those stay in private/ (never committed), so this
runs only on a machine that has them; tests/test_curated.py covers every Curated Parser with synthetic fixtures."""
import pytest

from tests.helpers import ROOT, run_harness

CURATED = ROOT / "parsers" / "curated"
PRIVATE = ROOT / "private" / "fixtures" / "curated"
FIXTURES = sorted(PRIVATE.glob("*.txt")) if PRIVATE.exists() else []


@pytest.mark.skipif(not FIXTURES, reason="no private fixtures on this machine")
@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda p: p.stem)
def test_curated_parser_reconciles_a_redacted_real_statement(tmp_path, fixture):
    result = run_harness(fixture, out=tmp_path, parsers=[CURATED])

    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith(f"PASS  {fixture.name}: ")
