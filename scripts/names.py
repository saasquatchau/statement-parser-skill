"""Builds a list of first names for scripts/redact.py, keeping only names of 3+ letters that aren't also
ordinary English words, so redaction catches people's names without wiping out words like CREDIT or HOTEL.

    python scripts/names.py <first names.txt> <out.txt> [--dictionary /usr/share/dict/words]

The dictionary lists proper names capitalised, so only its lowercase entries count as ordinary words. The list
stays in private/: the source list's origin and licence are unknown, so it isn't committed.
"""
import argparse
from pathlib import Path

MIN_LENGTH = 3
# The dictionary leaves out plurals and other inflections ("computers", "has"), so a word is also ordinary when
# taking one of these endings off leaves a dictionary word.
ENDINGS = ("s", "es", "ed", "ing")


def is_ordinary(word, ordinary):
    word = word.lower()
    return word in ordinary or any(word.endswith(e) and word[:-len(e)] in ordinary for e in ENDINGS)


def names(source, dictionary):
    ordinary = {w for w in Path(dictionary).read_text().split() if w.islower()}
    found = {n.upper() for n in Path(source).read_text().split() if len(n) >= MIN_LENGTH and not is_ordinary(n, ordinary)}
    return sorted(found)


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("source")
    cli.add_argument("out")
    cli.add_argument("--dictionary", default="/usr/share/dict/words")
    args = cli.parse_args()
    kept = names(args.source, args.dictionary)
    Path(args.out).write_text("\n".join(kept) + "\n")
    print(f"{len(kept)} names")
