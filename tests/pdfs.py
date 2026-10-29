"""Builds synthetic statement PDFs for tests, the same way the Cowork probe did."""


def make_pdf(path, lines):
    # Hand-built single-page PDF with a real text layer, so no PDF writer library is needed.
    escaped = [l.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for l in lines]
    stream = "BT /F1 10 Tf 40 800 Td 13 TL " + " ".join(f"({l}) '" for l in escaped) + " ET"
    return _write_pdf(path, stream)


def _write_pdf(path, stream):
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = "%PDF-1.4\n", []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n"
    with open(path, "w", encoding="latin-1") as f:
        f.write(out)
    return path


def pdf_from_fixture(fixture, directory):
    directory.mkdir(parents=True, exist_ok=True)
    return make_pdf(directory / f"{fixture.stem}.pdf", fixture.read_text().splitlines())


def scanned_pdf_from_fixture(fixture, directory):
    """A PDF with no text layer: the synthetic statement rendered to an image, as a scanner would produce."""
    import pypdfium2 as pdfium

    text_pdf = pdf_from_fixture(fixture, directory / "text-layer")
    image = pdfium.PdfDocument(str(text_pdf))[0].render(scale=3).to_pil()
    path = directory / f"{fixture.stem}-scanned.pdf"
    image.convert("RGB").save(path)
    return path


# Helvetica advance widths (per 1000 em) for the characters right-aligned amounts use.
AMOUNT_WIDTHS = {**{d: 556 for d in "0123456789"}, ",": 278, ".": 278}


def make_table_pdf(path, rows, size=10):
    """A single-page PDF that places each item where a real statement would: rows are lists of (x, text, align),
    where align "right" means x is the item's right edge, as for amounts in a column."""
    items = []
    for i, row in enumerate(rows):
        y = 800 - 13 * i
        for x, text, align in row:
            if align == "right":
                x -= sum(AMOUNT_WIDTHS.get(c, 556) for c in text) * size / 1000
            escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            items.append(f"BT /F1 {size} Tf {x:.2f} {y} Td ({escaped}) Tj ET")
    return _write_pdf(path, " ".join(items))
