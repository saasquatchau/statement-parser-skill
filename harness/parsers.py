"""Loads Parsers from their sources and picks the ones whose Signature matches a statement."""
import importlib.util
from pathlib import Path


def load_parser(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_parsers(directory):
    return [load_parser(path) for path in sorted(Path(directory).glob("*.py"))]


def matching(parsers, text, statement_format=None):
    """A named Statement Format only chooses between Parsers whose Signature matches (the bookkeeper's answer to
    an ASK); it can never force a Parser onto a statement it wasn't written for."""
    matches = [p for p in parsers if all(s in text for s in p.SIGNATURE)]
    if statement_format:
        return [p for p in matches if p.STATEMENT_FORMAT == statement_format]
    return matches
