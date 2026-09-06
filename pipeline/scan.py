"""OCR a book that was photographed as two-page spreads.

The Perio Górska 2022 PDF is a flat, sharp scan with no text layer, one image
per *spread*: a single PDF page holds two facing book pages. Tesseract reads it
well (~0.4% garbled tokens against the <2% gate) once each spread is cut in half
and rendered at 400 dpi — but only from a plain grayscale render. Binarizing to
recover the white-on-red page numbers costs real body text ("250 200 mg" for
"250-500 mg"), so this module never binarizes the body: the printed page numbers
come from a checked-in map instead.

data/pagemap/<book_id>.json carries the printed numbering, under "spreads"
when one PDF page holds two printed pages, or "pages" when it holds one (the
pedodontics kompendium is photographed a page at a time). A spread entry gives
the printed number of its *left* page; the right page is that plus one. The map
cannot be computed: the Perio scan mixes true spreads (verso|recto) with
misaligned captures (recto|verso), duplicates a few spreads and drops others,
and the kompendium scan skips 28 pages scattered through the book, so the
pdf-to-printed offset drifts from +6 to +28. PDF pages missing from the map
(duplicates, front matter) are skipped, and the pages they would carry simply
do not exist in the book's text file.

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
import numpy as np

# Allow running as a script as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PAGEMAP_DIR = Path("data/pagemap")
IMAGE_DIR = Path("data/images")
OCR_DPI = 400          # ~20 px glyphs; below this Tesseract starts dropping words
OCR_LANG = "pol"


def load_pagemap(book_id: str) -> tuple[dict[int, int], bool]:
    """({pdf page -> printed page number}, whether that PDF page is a spread)."""
    raw = json.loads((PAGEMAP_DIR / f"{book_id}.json").read_text(encoding="utf-8"))
    key = "spreads" if "spreads" in raw else "pages"
    return {int(k): v for k, v in raw[key].items()}, key == "spreads"


def gutter(page: fitz.Page) -> float:
    """Fraction of the page width where the binding shadow runs.

    The ortodoncja scan is bound off-centre: its gutter sits at ~0.52 of the
    width, and one page's text starts at 0.486 — so a midpoint clip cuts into
    the right-hand page. The shadow is by far the darkest column band, so it is
    found by looking for the peak of the ink profile in the middle fifth of the
    page. Detection outside 0.48-0.56 is not believed and the midpoint is used.
    """
    pix = page.get_pixmap(dpi=100, colorspace=fitz.csGRAY)
    grey = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    ink = 255 - grey.mean(axis=0)
    lo, hi = int(0.40 * pix.width), int(0.60 * pix.width)
    x = (lo + int(np.argmax(ink[lo:hi]))) / pix.width
    return x if 0.48 < x < 0.56 else 0.5


def halves(page: fitz.Page, find_gutter: bool = False) -> list[fitz.Rect]:
    """Left and right halves of a spread, cut at the midpoint or the gutter."""
    r = page.rect
    mid = (gutter(page) if find_gutter else 0.5) * r.width
    margin = 0.004 * r.width if find_gutter else 0
    return [fitz.Rect(0, 0, mid - margin, r.height),
            fitz.Rect(mid + margin, 0, r.width, r.height)]


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


def scan_book(pdf_path: Path, book: str, book_id: str, dehyphenate,
              find_gutter: bool = False) -> dict:
    """OCR every mapped page; same shape as extract.extract_book()."""
    pagemap, spreads = load_pagemap(book_id)
    out_dir = IMAGE_DIR / book_id
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = []
    for pdf_page, first_page in sorted(pagemap.items()):
        src = doc[pdf_page - 1]
        clips = halves(src, find_gutter) if spreads else [None]
        for offset, clip in enumerate(clips):
            number = first_page + offset
            img = out_dir / f"p{number:03d}.png"
            if not img.exists():   # rendering + OCR of 220 pages is slow
                src.get_pixmap(dpi=OCR_DPI, clip=clip).pil_save(img)
            pages.append({"page": number, "text": dehyphenate(ocr(img))})
    pages.sort(key=lambda p: p["page"])
    return {"book": book, "pages": pages}
