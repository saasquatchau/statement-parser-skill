"""Packages the statement-parser skill as an uploadable .skill file (a zip): SKILL.md, the library page, the
harness and the Curated Parsers.

    python scripts/build_skill.py [--out dist] [--demo]

--demo also bundles the synthetic Probe Bank Parser and writes a matching demo statement PDF, so the skill can be
tried in Claude chat before any Curated Parsers exist.
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

NAME = "statement-parser"


def build(out, demo):
    staging = out / NAME
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    shutil.copy(ROOT / "skill" / "SKILL.md", staging / "SKILL.md")
    shutil.copy(ROOT / "skill" / "BUILD.md", staging / "BUILD.md")
    shutil.copytree(ROOT / "skill" / "library", staging / "library")
    shutil.copytree(ROOT / "harness", staging / "harness", ignore=shutil.ignore_patterns("__pycache__"))
    curated = staging / "parsers" / "curated"
    shutil.copytree(ROOT / "parsers" / "curated", curated, ignore=shutil.ignore_patterns("__pycache__", "*.md"))
    if demo:
        from tests.pdfs import pdf_from_fixture

        shutil.copy(ROOT / "tests" / "parsers" / "probe_bank_deposit.py", curated)
        pdf_from_fixture(ROOT / "tests" / "fixtures" / "probe-deposit-march.txt", out)
        (out / "probe-deposit-march.pdf").rename(out / "demo-statement.pdf")
    archive = out / f"{NAME}.skill"  # a zip; Claude accepts it as a skill upload
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(staging.rglob("*")):
            z.write(path, path.relative_to(out))
    return archive


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--out", default=str(ROOT / "dist"))
    cli.add_argument("--demo", action="store_true")
    args = cli.parse_args()
    print(build(Path(args.out), args.demo))
