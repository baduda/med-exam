"""Extract per-page source material from the PDFs — text, or page images.

No chapter/section detection — the books are dense and irregularly structured,
so downstream chunking uses simple word windows over consecutive pages
(see chunk.py). Each page keeps its 1-based page number for source references.

Books declared `mode: "image"` in books.py have no usable text layer and cannot
be OCR'd (see the note there). For those, pages are rendered to JPEG under
data/images/<book_id>/ and the per-page record carries an image path instead of
text; the generating agent reads the images. Rendering uses the images' native
resolution — upsampling a 96 dpi photo adds pixels, not legibility.
"""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

# Allow running as a script (`python pipeline/extract.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.books import lookup, mode

BOOKS_DIR = Path("books")
OUT_DIR = Path("data/text")
IMAGE_DIR = Path("data/images")
RENDER_DPI = 100   # ~native for the Periodontologia photos (517x768 pt / 689x1024 px)
JPEG_QUALITY = 80


def dehyphenate(text: str) -> str:
    """Join line-break hyphenation and collapse whitespace to single spaces."""
    text = re.sub(r"-[ \t]*\n", "", text)    # join hyphenated line breaks
    text = re.sub(r"\n+", " ", text)          # remaining newlines -> spaces
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_book(pdf_path: Path, book: str) -> dict:
    """Return {"book": "Tom2", "pages": [{"page": 1, "text": "..."}, ...]}."""
    doc = fitz.open(pdf_path)
    pages = [{"page": i + 1, "text": dehyphenate(doc[i].get_text())}
             for i in range(doc.page_count)]
    return {"book": book, "pages": pages}


def render_book(pdf_path: Path, book: str, book_id: str) -> dict:
    """Render every page to JPEG; return the same shape as extract_book(), with
    an "image" path per page and an empty "text"."""
    out_dir = IMAGE_DIR / book_id
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages = []
    for i in range(doc.page_count):
        img = out_dir / f"p{i + 1:03d}.jpg"
        if not img.exists():   # rendering 541 photos is slow; make re-runs cheap
            doc[i].get_pixmap(dpi=RENDER_DPI).pil_save(img, quality=JPEG_QUALITY)
        pages.append({"page": i + 1, "text": "", "image": str(img)})
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
        else:
            data = extract_book(pdf, entry["book"])
            kind = f"{sum(1 for p in data['pages'] if p['text'])} of " \
                   f"{len(data['pages'])} pages with text"
        out = OUT_DIR / f"{data['book']}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{pdf.name}: {kind} -> {out}")


if __name__ == "__main__":
    sys.exit(main())
