"""Extract cleaned per-page text from the source PDFs.

No chapter/section detection — the books are dense and irregularly structured,
so downstream chunking uses simple word windows over consecutive pages
(see chunk.py). Each page keeps its 1-based page number for source references.
"""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

# Allow running as a script (`python pipeline/extract.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.books import lookup

BOOKS_DIR = Path("books")
OUT_DIR = Path("data/text")


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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(BOOKS_DIR.glob("*.pdf")):
        entry = lookup(pdf.name)
        if entry is None:
            print(f"{pdf.name}: ignored (see pipeline/books.py)")
            continue
        data = extract_book(pdf, entry["book"])
        out = OUT_DIR / f"{data['book']}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        nonempty = sum(1 for p in data["pages"] if p["text"])
        print(f"{pdf.name}: {len(data['pages'])} pages ({nonempty} with text) -> {out}")


if __name__ == "__main__":
    sys.exit(main())
