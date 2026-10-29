"""Turns a statement input (PDF or extracted-text fixture) into text for Parsers."""
import re
from pathlib import Path

AMOUNT_WORD = re.compile(r"^[\d,]*\d\.\d{2}$")
# The same amounts found in a line of text; a dot leader may run straight into one ("....17,811.09").
AMOUNT_IN_TEXT = re.compile(r"(?<![\d,])(?<!\d\.)[\d,]*\d\.\d{2}(?!\d)")


def statement_pages(path, columns=()):
    """Returns (pages, scanned): the text of each page. A PDF with no text layer is read by OCR and reported as
    scanned. A text fixture is one page. With `columns` (a Parser's COLUMNS), each amount printed under one of
    those headings is tagged with it ("Credits:17,811.09"); a text fixture carries its tags already."""
    path = Path(path)
    if path.suffix.lower() != ".pdf":
        return [path.read_text()], False
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        if columns:
            pages, spans = [], {}
            for page in pdf.pages:
                spans = heading_spans(page.extract_words(), columns) or spans
                pages.append(tagged_page_text(page, spans))
        else:
            pages = [page.extract_text() or "" for page in pdf.pages]
    if any(p.strip() for p in pages):
        return pages, False
    return ocr_pages(path), True


def statement_text(path, columns=()):
    pages, scanned = statement_pages(path, columns)
    return "\n".join(pages), scanned


def parser_text(path, parser, text):
    """The text `parser` reads: `text` (the statement's plain text), or the column-tagged text if it declares
    COLUMNS."""
    columns = getattr(parser, "COLUMNS", ())
    return statement_text(path, columns)[0] if columns else text


def heading_spans(words, columns):
    """{heading: (x0, x1)} for each heading found on the page, taking its first occurrence (the column titles).
    A heading of several words must be printed on one line, in order."""
    spans = {}
    for heading in columns:
        tokens = heading.split()
        for i in range(len(words) - len(tokens) + 1):
            run = words[i:i + len(tokens)]
            if [w["text"] for w in run] == tokens and all(abs(w["top"] - run[0]["top"]) < 1 for w in run):
                spans[heading] = (run[0]["x0"], run[-1]["x1"])
                break
    return spans


def tagged_page_text(page, spans):
    """The page's text, line by line, with each amount that sits under exactly one heading tagged with it. A line
    whose amounts can't be lined up with its words is left untagged, so the Parser fails rather than guesses."""
    words = page.extract_words()
    lines = []
    for line in page.extract_text_lines():
        amounts = sorted((w for w in words if line["top"] - 1 <= w["top"] <= line["bottom"]
                          and AMOUNT_WORD.match(w["text"])), key=lambda w: w["x0"])
        matches = list(AMOUNT_IN_TEXT.finditer(line["text"]))
        text = line["text"]
        if len(amounts) == len(matches):
            for word, match in reversed(list(zip(amounts, matches))):
                under = [h for h, (x0, x1) in spans.items() if word["x0"] < x1 and word["x1"] > x0]
                if len(under) == 1:
                    text = f"{text[:match.start()]}{under[0]}:{text[match.start():]}"
        lines.append(text)
    return "\n".join(lines)


def ocr_pages(path):
    import pypdfium2 as pdfium
    import pytesseract

    return [pytesseract.image_to_string(page.render(scale=3).to_pil()) for page in pdfium.PdfDocument(str(path))]
