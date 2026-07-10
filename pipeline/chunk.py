"""Split each book's pages into ~700-word chunks over consecutive pages.

No chapter logic: we accumulate page text until the word target is reached,
then emit a chunk carrying its [start, end] page range for source references.
Writes one file per chunk to data/chunks/ and a resumable data/state.json.
"""
import json
import sys
from pathlib import Path

TEXT_DIR = Path("data/text")
CHUNK_DIR = Path("data/chunks")
STATE_FILE = Path("data/state.json")
TARGET_WORDS = 700


def book_prefix(book: str) -> str:
    """'Tom2' -> 't2' (t + volume number)."""
    digits = "".join(c for c in book if c.isdigit())
    return f"t{digits}"


def chunk_pages(pages: list[dict], target_words: int = TARGET_WORDS) -> list[dict]:
    """Group consecutive pages into {'pages': [start, end], 'text': str} chunks."""
    chunks: list[dict] = []
    buf_texts: list[str] = []
    start_page = None
    end_page = None
    words = 0
    for pg in pages:
        text = pg["text"].strip()
        if not text:
            continue
        if start_page is None:
            start_page = pg["page"]
        end_page = pg["page"]
        buf_texts.append(text)
        words += len(text.split())
        if words >= target_words:
            chunks.append({"pages": [start_page, end_page], "text": " ".join(buf_texts)})
            buf_texts, start_page, end_page, words = [], None, None, 0
    if buf_texts:
        chunks.append({"pages": [start_page, end_page], "text": " ".join(buf_texts)})
    return chunks


def main() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    state = {"chunks": {}}
    for text_file in sorted(TEXT_DIR.glob("*.json")):
        data = json.loads(text_file.read_text(encoding="utf-8"))
        prefix = book_prefix(data["book"])
        for i, ch in enumerate(chunk_pages(data["pages"]), 1):
            cid = f"{prefix}-c{i:03d}"
            chunk = {"chunk_id": cid, "book": data["book"],
                     "pages": ch["pages"], "text": ch["text"]}
            (CHUNK_DIR / f"{cid}.json").write_text(
                json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
            state["chunks"][cid] = {"book": data["book"], "pages": ch["pages"],
                                    "words": len(ch["text"].split()), "generated": False}
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(state['chunks'])} chunks -> {CHUNK_DIR}")


if __name__ == "__main__":
    sys.exit(main())
