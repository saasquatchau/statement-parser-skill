import subprocess
import sys
import zipfile

from tests.helpers import FIXTURES, ROOT
from tests.pdfs import pdf_from_fixture


def build_skill(out, *options):
    return subprocess.run([sys.executable, "scripts/build_skill.py", "--out", str(out), *options],
                          cwd=ROOT, capture_output=True, text=True)


def test_packaged_skill_runs_its_bundled_parsers_from_its_own_folder(tmp_path):
    build = build_skill(tmp_path / "dist", "--demo")
    assert build.returncode == 0, build.stderr

    with zipfile.ZipFile(tmp_path / "dist" / "statement-parser.skill") as z:
        z.extractall(tmp_path / "installed")
    skill = tmp_path / "installed" / "statement-parser"
    assert (skill / "SKILL.md").read_text().startswith("---\nname: statement-parser\n")

    statement = pdf_from_fixture(FIXTURES / "probe-deposit-march.txt", tmp_path / "uploads")
    result = subprocess.run(
        [sys.executable, "-m", "harness", "run", str(statement), "--parsers", "parsers/curated", "--out", str(tmp_path / "outputs")],
        cwd=skill, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[-1] == "CSV   Probe-Bank-DEP-xx5678-2026-03.csv: 1 statement, 3 transactions"


def test_packaged_skill_contains_no_tests_or_fixtures(tmp_path):
    build_skill(tmp_path / "dist")

    with zipfile.ZipFile(tmp_path / "dist" / "statement-parser.skill") as z:
        names = z.namelist()
    assert not [n for n in names if "/tests/" in n or n.endswith(".txt") or "__pycache__" in n]


def test_packaged_skill_carries_the_library_page_for_setup(tmp_path):
    build_skill(tmp_path / "dist")

    with zipfile.ZipFile(tmp_path / "dist" / "statement-parser.skill") as z:
        page = z.read("statement-parser/library/index.html").decode()
    assert 'claude.use("db")' in page
    assert 'collection("parsers")' in page


def test_packaged_skill_carries_the_build_guide(tmp_path):
    build_skill(tmp_path / "dist")

    with zipfile.ZipFile(tmp_path / "dist" / "statement-parser.skill") as z:
        guide = z.read("statement-parser/BUILD.md").decode()
    assert guide.startswith("# Writing a Parser")
