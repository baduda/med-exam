"""Extract cleaned, chapter-split text from the source PDFs."""
import json
import re
import sys
from pathlib import Path

import fitz  # pymupdf

BOOKS_DIR = Path("books")
OUT_DIR = Path("data/text")
# Chapter heading at line start: "9. Title" or "12.3. Title" — we treat the
# top-level "N. Title" as chapter boundary.
HEADING_RE = re.compile(r"^(\d+)\.\s+(.+)$", re.MULTILINE)


def dehyphenate(text: str) -> str:
    text = re.sub(r"-\n", "", text)          # join hyphenated line breaks
    text = re.sub(r"\n+", " ", text)          # remaining newlines -> spaces
    return re.sub(r"[ \t]+", " ", text).strip()


def split_chapters(pages: list[dict]) -> list[dict]:
    """Group pages into chapters by the first top-level 'N. Title' heading seen."""
    chapters: list[dict] = []
    current = None
    for pg in pages:
        m = HEADING_RE.search(pg["text"])
        if m:
            if current:
                chapters.append(current)
            current = {"chapter": m.group(1), "title": m.group(2).strip(),
                       "pages": [pg["page"], pg["page"]], "text": ""}
        if current is None:
            current = {"chapter": "0", "title": "front", "pages": [pg["page"], pg["page"]], "text": ""}
        current["pages"][1] = pg["page"]
        current["text"] += "\n" + pg["text"]
    if current:
        chapters.append(current)
    for c in chapters:
        c["text"] = dehyphenate(c["text"])
    return chapters


def extract_book(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    pages = [{"page": i + 1, "text": doc[i].get_text()} for i in range(doc.page_count)]
    book = pdf_path.stem.split(".")[0].strip()  # "Tom2. Mansur Rahnama" -> "Tom2"
    return {"book": book, "chapters": split_chapters(pages)}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(BOOKS_DIR.glob("*.pdf")):
        data = extract_book(pdf)
        out = OUT_DIR / f"{data['book']}.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{pdf.name}: {len(data['chapters'])} chapters -> {out}")


if __name__ == "__main__":
    sys.exit(main())
