"""Environment probe for the statement-parser skill in Cowork.

Prints one short line per check. Never prints file contents beyond the probe's own test data.
"""
import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

results = []


def report(name, ok, detail=""):
    mark = "PASS" if ok is True else "FAIL" if ok is False else "INFO"
    results.append(f"{mark:4}  {name}: {detail}")


def make_pdf(path, lines):
    # Hand-built single-page PDF with a real text layer, so no PDF writer library is needed.
    stream = "BT /F1 12 Tf 72 720 Td 14 TL " + " ".join(f"({l}) '" for l in lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
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


def main():
    lib = sys.argv[1] if len(sys.argv) > 1 else None
    # Per-run temp dir: a fixed /tmp path collides with files left by earlier Cowork sessions.
    work = tempfile.mkdtemp(prefix="cowork-probe-")

    # 1. Runtime
    report("python", True, f"{platform.python_version()} on {platform.system()} {platform.machine()}")
    for mod in ["pdfplumber", "pypdf", "pypdfium2", "pdfminer", "pytesseract", "PIL", "fitz"]:
        try:
            m = importlib.import_module(mod)
            report(f"import {mod}", True, getattr(m, "__version__", "ok"))
        except Exception as e:
            report(f"import {mod}", False, type(e).__name__)
    report("tesseract binary", bool(shutil.which("tesseract")), shutil.which("tesseract") or "not on PATH")
    report("ocrmypdf binary", bool(shutil.which("ocrmypdf")), shutil.which("ocrmypdf") or "not on PATH")

    # 2. Network / pip (dry run only, installs nothing)
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "download", "--no-deps", "-d", os.path.join(work, "pip"), "six", "-q"],
            capture_output=True, timeout=45,
        )
        report("pip can reach PyPI", r.returncode == 0, "yes" if r.returncode == 0 else "no (network blocked or pip missing)")
    except Exception as e:
        report("pip can reach PyPI", False, type(e).__name__)

    # 3. Text extraction on a synthetic statement
    tmp = os.path.join(work, "probe-statement.pdf")
    make_pdf(tmp, ["PROBE BANK STATEMENT", "OPENING BALANCE 100.00", "COFFEE -4.50", "CLOSING BALANCE 95.50"])
    text = None
    try:
        import pdfplumber
        with pdfplumber.open(tmp) as pdf:
            text = pdf.pages[0].extract_text() or ""
        report("pdfplumber extracts text", "CLOSING BALANCE 95.50" in text, "matched" if "95.50" in text else "no match")
    except Exception as e:
        report("pdfplumber extracts text", False, type(e).__name__)

    # 4. OCR round trip: render the page to an image, OCR it
    try:
        import pypdfium2 as pdfium
        import pytesseract
        img = pdfium.PdfDocument(tmp)[0].render(scale=3).to_pil()
        ocr = pytesseract.image_to_string(img)
        report("OCR round trip", "95.50" in ocr, "read the closing balance" if "95.50" in ocr else "did not read it")
    except Exception as e:
        report("OCR round trip", False, type(e).__name__)

    # 5. Parser Library folder: write, execute from folder, persistence
    if not lib:
        report("library folder", False, "no folder path given")
    elif not os.path.isdir(lib):
        report("library folder", False, f"not a directory: {lib}")
    else:
        lowered = lib.lower()
        synced = [s for s in ["dropbox", "onedrive", "google drive", "googledrive", "cloudstorage", "sharepoint", "icloud"] if s in lowered]
        report("library folder", True, f"{lib} (looks synced: {', '.join(synced) or 'no'})")
        d = os.path.join(lib, "statement-parser-probe")
        marker = os.path.join(d, "runs.json")
        try:
            os.makedirs(d, exist_ok=True)
            runs = json.load(open(marker)) if os.path.exists(marker) else []
            report("persisted_from_earlier_run", bool(runs) or None,
                   f"{len(runs)} earlier run(s), last {runs[-1]}" if runs else "first run (re-run in a NEW task to test)")
            runs.append(datetime.now(timezone.utc).isoformat(timespec="seconds"))
            with open(marker, "w") as f:
                json.dump(runs, f)
            parser = os.path.join(d, "probe_parser.py")
            with open(parser, "w") as f:
                f.write("import sys\nprint('parser-ran', len(open(sys.argv[1],'rb').read()))\n")
            t = time.time()
            r = subprocess.run([sys.executable, parser, tmp], capture_output=True, text=True, timeout=30)
            ok = r.returncode == 0 and r.stdout.startswith("parser-ran")
            report("run script stored in library folder", ok, f"{(time.time() - t) * 1000:.0f} ms" if ok else (r.stderr.strip()[-120:] or "failed"))
            tmpname = parser + ".tmp"
            with open(tmpname, "w") as f:
                f.write("# atomic rename test\n")
            os.replace(tmpname, os.path.join(d, "renamed.py"))
            report("atomic rename in folder", True, "ok")
        except Exception as e:
            report("library folder write/run", False, f"{type(e).__name__}: {e}"[:160])

    print("cowork-probe " + datetime.now(timezone.utc).isoformat(timespec="seconds"))
    print("\n".join(results))


main()
