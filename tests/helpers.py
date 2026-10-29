import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
PARSERS = ROOT / "tests" / "parsers"


def run_harness(*statements, out, parsers=(PARSERS,), options=()):
    sources = [arg for p in parsers for arg in ("--parsers", str(p))]
    return subprocess.run(
        [sys.executable, "-m", "harness", "run", *map(str, statements), *sources, "--out", str(out), *options],
        cwd=ROOT, capture_output=True, text=True,
    )


def only_csv(directory):
    """The text of the single CSV a Run wrote into `directory`."""
    (path,) = Path(directory).glob("*.csv")
    return path.read_text()
