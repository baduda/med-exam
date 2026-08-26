"""Extract per-page source material from the PDFs — text, or page images.

No chapter/section detection — the books are dense and irregularly structured,
so downstream chunking uses simple word windows over consecutive pages
(see chunk.py). Each page keeps its 1-based page number for source references.

Books that do not fit the plain one-page-one-record shape take another route
(see books.py). A `mode: "spread"` book has a text layer but two printed pages
per PDF page. A `mode: "scan"` book is OCR'd here via scan.py. A `mode: "image"` book cannot be
OCR'd at all, so its pages are rendered to JPEG under data/images/<book_id>/ and
the per-page record carries an image path instead of text; an agent reads the
images (see transcribe.py). Rendering those uses the images' native resolution —
upsampling a 96 dpi photo adds pixels, not legibility.
"""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

# Allow running as a script (`python pipeline/extract.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.books import lookup, mode
from pipeline.scan import scan_book

BOOKS_DIR = Path("books")
OUT_DIR = Path("data/text")
IMAGE_DIR = Path("data/images")
RENDER_DPI = 100   # ~native for the Periodontologia photos (517x768 pt / 689x1024 px)
JPEG_QUALITY = 80


def dehyphenate(text: str) -> str:
    """Join line-break hyphenation and collapse whitespace to single spaces.

    Majewski's OCR marks hyphenation with a SOFT HYPHEN (U+00AD) rather than "-",
    both at line breaks and mid-line; left in, it reads as 5% garbled tokens
    ("kształ\xadtowanie") against a <2% gate. No other source book contains one.
    """
    text = text.replace("\u00ad\n", "").replace("\u00ad", "")
    text = re.sub(r"-[ \t]*\n", "", text)    # join hyphenated line breaks
    text = re.sub(r"\n+", " ", text)          # remaining newlines -> spaces
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_book(pdf_path: Path, book: str) -> dict:
    """Return {"book": "Tom2", "pages": [{"page": 1, "text": "..."}, ...]}."""
    doc = fitz.open(pdf_path)
    pages = [{"page": i + 1, "text": dehyphenate(doc[i].get_text())}
             for i in range(doc.page_count)]
    return {"book": book, "pages": pages}


def extract_spread_book(pdf_path: Path, book: str) -> dict:
    """Like extract_book(), but one PDF page carries two facing printed pages.

    The Dejak vademecum is typeset as spreads, rotated 90 degrees, with the
    printed numbering `left = 2 * pdf_page - 2` (verified at pdf 4->6, 11->20,
    51->100, 151->300, 197->392). The spread is NOT split geometrically: the
    gutter is off-centre, so a midpoint clip cuts words in half
    ("powierzchnia" -> "owierzchnia"), and clustering blocks back into two
    columns buys only +/-1 page of precision. Each spread is emitted whole and
    numbered with its left printed page, so a citation names the spread that
    carries the text. The text layer is the publisher's own, so reading order
    across the spread is already correct.
    """
    doc = fitz.open(pdf_path)
    pages = [{"page": max(1, 2 * (i + 1) - 2),
              "text": dehyphenate(doc[i].get_text())}
             for i in range(doc.page_count)]
    return {"book": book, "pages": pages}


def existing_text(book: str) -> dict[int, str]:
    """Text already in data/text/<Book>.json, keyed by page number.

    An image book's text is written by agents through transcribe.py, and it is
    the only copy — nothing can regenerate it. A re-run of extract.py must
    therefore carry it forward rather than reset every page to "".
    """
    out = OUT_DIR / f"{book}.json"
    if not out.exists():
        return {}
    data = json.loads(out.read_text(encoding="utf-8"))
    return {p["page"]: p.get("text", "") for p in data["pages"]}


def render_book(pdf_path: Path, book: str, book_id: str) -> dict:
    """Render every page to JPEG; return the same shape as extract_book(), with
    an "image" path per page. Any transcription already on disk is preserved."""
    out_dir = IMAGE_DIR / book_id
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = existing_text(book)
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(doc.page_count):
        img = out_dir / f"p{i + 1:03d}.jpg"
        if not img.exists():   # rendering 541 photos is slow; make re-runs cheap
            doc[i].get_pixmap(dpi=RENDER_DPI).pil_save(img, quality=JPEG_QUALITY)
        pages.append({"page": i + 1, "text": kept.get(i + 1, ""), "image": str(img)})
    return {"book": book, "pages": pages}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(BOOKS_DIR.glob("*.pdf")):
        entry = lookup(pdf.name)
        if entry is None:
            print(f"{pdf.name}: ignored (see pipeline/books.py)")
            continue
        if mode(entry) == "image":
            data = render_book(pdf, entry["book"], entry["book_id"])
            kind = f"{len(data['pages'])} page images"
        elif mode(entry) == "spread":
            data = extract_spread_book(pdf, entry["book"])
            kind = f"{len(data['pages'])} spreads -> printed pages " \
                   f"{data['pages'][0]['page']}-{data['pages'][-1]['page'] + 1}"
        elif mode(entry) == "scan":
            data = scan_book(pdf, entry["book"], entry["book_id"], dehyphenate)
            kind = f"{len(data['pages'])} pages OCR'd from spreads"
        else:
            data = extract_book(pdf, entry["book"])
            kind = f"{sum(1 for p in data['pages'] if p['text'])} of " \
                   f"{len(data['pages'])} pages with text"
        out = OUT_DIR / f"{data['book']}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{pdf.name}: {kind} -> {out}")


if __name__ == "__main__":
    sys.exit(main())
