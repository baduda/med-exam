"""OCR a book that was photographed as two-page spreads.

The Perio Górska 2022 PDF is a flat, sharp scan with no text layer, one image
per *spread*: a single PDF page holds two facing book pages. Tesseract reads it
well (~0.4% garbled tokens against the <2% gate) once each spread is cut in half
and rendered at 400 dpi — but only from a plain grayscale render. Binarizing to
recover the white-on-red page numbers costs real body text ("250 200 mg" for
"250-500 mg"), so this module never binarizes the body: the printed page numbers
come from a checked-in map instead.

data/pagemap/<book_id>.json maps each spread to the printed number of its left
page; the right page is that plus one. The map cannot be computed, because the
scan mixes true spreads (verso|recto) with misaligned captures (recto|verso),
duplicates a few spreads and drops others — so it was read off the header bands
by eye and frozen here. Spreads missing from the map (duplicates, front matter)
are skipped, and the pages they would carry simply do not exist in the book's
text file.

Rendered halves and their OCR text are both cached under data/images/<book_id>/ —
Tesseract needs ~10 s per page, so without the .txt cache a re-run of extract.py
would cost half an hour of CPU to reproduce a file it already has.

    python pipeline/extract.py        # runs this for `mode: "scan"` books
"""
import json
import subprocess
import sys
from pathlib import Path

import fitz  # pymupdf

# Allow running as a script as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PAGEMAP_DIR = Path("data/pagemap")
IMAGE_DIR = Path("data/images")
OCR_DPI = 400          # ~20 px glyphs; below this Tesseract starts dropping words
OCR_LANG = "pol"


def load_pagemap(book_id: str) -> dict[int, int]:
    """{spread number -> printed page number of its left half}."""
    raw = json.loads((PAGEMAP_DIR / f"{book_id}.json").read_text(encoding="utf-8"))
    return {int(k): v for k, v in raw["spreads"].items()}


def halves(page: fitz.Page) -> list[fitz.Rect]:
    """Left and right halves of a spread."""
    r = page.rect
    mid = r.width / 2
    return [fitz.Rect(0, 0, mid, r.height), fitz.Rect(mid, 0, r.width, r.height)]


def ocr(image: Path) -> str:
    """OCR one page image, caching the result beside it."""
    cache = image.with_suffix(".txt")
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    out = subprocess.run(
        ["tesseract", str(image), "-", "-l", OCR_LANG, "--psm", "3"],
        capture_output=True, text=True, check=True)
    cache.write_text(out.stdout, encoding="utf-8")
    return out.stdout


def scan_book(pdf_path: Path, book: str, book_id: str, dehyphenate) -> dict:
    """OCR every mapped spread half; same shape as extract.extract_book()."""
    pagemap = load_pagemap(book_id)
    out_dir = IMAGE_DIR / book_id
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = []
    for spread, first_page in sorted(pagemap.items()):
        src = doc[spread - 1]
        for offset, clip in enumerate(halves(src)):
            number = first_page + offset
            img = out_dir / f"p{number:03d}.png"
            if not img.exists():   # rendering + OCR of 220 pages is slow
                src.get_pixmap(dpi=OCR_DPI, clip=clip).pil_save(img)
            pages.append({"page": number, "text": dehyphenate(ocr(img))})
    pages.sort(key=lambda p: p["page"])
    return {"book": book, "pages": pages}
