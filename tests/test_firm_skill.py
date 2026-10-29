import json
import os
import shutil
import stat
import subprocess
import sys
import zipfile

from tests.helpers import FIXTURES, ROOT
from tests.pdfs import pdf_from_fixture

LIBRARY = "https://claude.ai/artifact/AbC123xyz"
# The demo skill bundles every Curated Parser plus the synthetic Probe Bank one.
DEMO_BUNDLED = len(list((ROOT / "parsers" / "curated").glob("*.py"))) + 1


def installed_skill(tmp_path):
    """The demo skill unzipped and made read-only, as skills are in Claude's sandbox."""
    subprocess.run([sys.executable, "scripts/build_skill.py", "--out", str(tmp_path / "dist"), "--demo"],
                   cwd=ROOT, check=True, capture_output=True)
    with zipfile.ZipFile(tmp_path / "dist" / "statement-parser.zip") as z:
        z.extractall(tmp_path / "installed")
    skill = tmp_path / "installed" / "statement-parser"
    for path in [skill, *skill.rglob("*")]:
        path.chmod(path.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    return skill


def harness(skill, *args):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run([sys.executable, "-m", "harness", *map(str, args)], cwd=skill, capture_output=True,
                          text=True, env=env)


def test_firm_skill_is_the_installed_skill_plus_the_firms_library_address(tmp_path):
    skill = installed_skill(tmp_path)
    result = harness(skill, "firm-skill", "--library", LIBRARY, "--firm", "Example Bookkeeping", "--out", tmp_path / "outputs")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"SKILL statement-parser.zip: Firm Skill v1 for Example Bookkeeping, {DEMO_BUNDLED} Bundled Parsers",
    ]
    with zipfile.ZipFile(tmp_path / "outputs" / "statement-parser.zip") as z:
        z.extractall(tmp_path / "firm")
    firm_skill = tmp_path / "firm" / "statement-parser"
    assert json.loads((firm_skill / "firm.json").read_text()) == {
        "firm": "Example Bookkeeping", "library": LIBRARY, "version": 1,
    }

    statement = pdf_from_fixture(FIXTURES / "probe-deposit-march.txt", tmp_path / "uploads")
    run = harness(firm_skill, "run", statement, "--parsers", "parsers/curated", "--out", tmp_path / "csv")
    assert run.returncode == 0, run.stdout + run.stderr


def test_firm_skill_refuses_an_address_that_is_not_a_claude_artifact(tmp_path):
    skill = installed_skill(tmp_path)
    result = harness(skill, "firm-skill", "--library", "https://example.com/library", "--firm", "Example Bookkeeping",
                     "--out", tmp_path / "outputs")

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "FAIL  firm-skill: library must be a claude.ai artifact link (https://claude.ai/artifact/...)",
    ]
    assert not (tmp_path / "outputs").exists()


def firm_skill(tmp_path):
    """The demo skill rebuilt as a Firm Skill and unzipped, as installed for a firm."""
    skill = installed_skill(tmp_path)
    harness(skill, "firm-skill", "--library", LIBRARY, "--firm", "Example Bookkeeping", "--out", tmp_path / "outputs")
    with zipfile.ZipFile(tmp_path / "outputs" / "statement-parser.zip") as z:
        z.extractall(tmp_path / "firm")
    return tmp_path / "firm" / "statement-parser"


def test_firm_skill_run_says_to_try_the_library_when_a_statement_did_not_reconcile(tmp_path):
    skill = firm_skill(tmp_path)
    redesigned = pdf_from_fixture(FIXTURES / "probe-deposit-2027-layout.txt", tmp_path / "uploads")
    result = harness(skill, "run", redesigned, "--parsers", "parsers/curated", "--out", tmp_path / "csv")

    assert result.stdout.splitlines()[-1] == (
        f"NEXT  1 statement may have a Firm Parser: follow \"Firm Parsers\" in SKILL.md (library {LIBRARY})"
    )


def test_no_library_hint_once_firm_parsers_were_tried(tmp_path):
    skill = firm_skill(tmp_path)
    unknown = FIXTURES / "unknown-bank.txt"
    result = harness(skill, "run", unknown, "--parsers", "parsers/curated", "--firm-parsers", tmp_path / "none",
                     "--out", tmp_path / "csv")

    assert not [line for line in result.stdout.splitlines() if line.startswith("NEXT")]


def promote(skill, firm_parsers, out):
    return harness(skill, "firm-skill", "--promote", firm_parsers, "--out", out)


def unzip(archive, into):
    with zipfile.ZipFile(archive) as z:
        z.extractall(into)
    return into / "statement-parser"


def test_promotion_bundles_firm_parsers_into_the_next_firm_skill_version(tmp_path):
    skill = firm_skill(tmp_path)
    fetched = tmp_path / "fetched"
    fetched.mkdir()
    shutil.copy(ROOT / "tests" / "parsers_firm" / "probe_bank_deposit_2027.py", fetched)
    shutil.copy(ROOT / "tests" / "parsers" / "probe_card.py", fetched)

    result = promote(skill, fetched, tmp_path / "promoted-zip")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines() == [
        f"SKILL statement-parser.zip: Firm Skill v2 for Example Bookkeeping, {DEMO_BUNDLED + 2} Bundled Parsers",
        "PROMOTED probe_bank_deposit_2027, probe_card: set promoted_in to \"v2\" on their library rows",
    ]
    promoted = unzip(tmp_path / "promoted-zip" / "statement-parser.zip", tmp_path / "v2")
    assert sorted(p.name for p in (promoted / "parsers" / "promoted").glob("*.py")) == [
        "probe_bank_deposit_2027.py", "probe_card.py",
    ]
    assert json.loads((promoted / "firm.json").read_text())["version"] == 2


def test_promotion_refuses_a_parser_containing_a_long_number(tmp_path):
    skill = firm_skill(tmp_path)
    fetched = tmp_path / "fetched"
    fetched.mkdir()
    shutil.copy(ROOT / "tests" / "parsers_firm" / "probe_bank_deposit_2027.py", fetched)
    shutil.copy(ROOT / "tests" / "parsers_leaky" / "probe_bank_leaky.py", fetched)

    result = promote(skill, fetched, tmp_path / "promoted-zip")

    assert result.returncode != 0
    assert result.stdout.splitlines() == [
        "REJECT probe_bank_leaky: Leak Scan found a long number in the Parser; nothing was promoted",
    ]
    assert not (tmp_path / "promoted-zip").exists()


def promoted_skill(tmp_path):
    skill = firm_skill(tmp_path)
    fetched = tmp_path / "fetched"
    fetched.mkdir()
    shutil.copy(ROOT / "tests" / "parsers_firm" / "probe_bank_deposit_2027.py", fetched)
    promote(skill, fetched, tmp_path / "promoted-zip")
    return unzip(tmp_path / "promoted-zip" / "statement-parser.zip", tmp_path / "v2")


def test_promoted_parser_runs_without_the_library(tmp_path):
    skill = promoted_skill(tmp_path)
    redesigned = pdf_from_fixture(FIXTURES / "probe-deposit-2027-layout.txt", tmp_path / "uploads")
    result = harness(skill, "run", redesigned, "--parsers", "parsers/curated", "--parsers", "parsers/promoted",
                     "--out", tmp_path / "csv")

    assert result.returncode == 0, result.stdout
    assert result.stdout.startswith("PASS  probe-deposit-2027-layout.pdf: Probe Bank deposit 2027 layout,")
    assert not [line for line in result.stdout.splitlines() if line.startswith(("NEXT", "TIP"))]


def test_detect_never_fetches_a_parser_this_skill_already_bundles(tmp_path):
    skill = promoted_skill(tmp_path)
    result = harness(skill, "detect", FIXTURES / "probe-deposit-2027-layout.txt",
                     "--signatures", FIXTURES / "library-signatures.json")

    assert result.stdout.splitlines() == ["NONE  probe-deposit-2027-layout.txt: nothing to fetch from the library"]
