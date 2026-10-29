import subprocess
import sys

from tests.helpers import FIXTURES, ROOT


def test_name_list_keeps_names_of_three_letters_or_more_that_are_not_ordinary_words(tmp_path):
    out = tmp_path / "names.txt"
    result = subprocess.run(
        [sys.executable, "scripts/names.py", str(FIXTURES / "names-sample.txt"), str(out),
         "--dictionary", str(FIXTURES / "dictionary-sample.txt")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0, result.stderr
    # AL is too short; CREDIT and HOTEL are ordinary words, and so are COMPUTERS and BOXES (plurals the dictionary
    # leaves out); Helen is capitalised in the dictionary, so a name.
    assert out.read_text().split() == ["ACME", "HELEN"]
