"""Split each book's pages into ~700-word chunks over consecutive pages.

No chapter logic: we accumulate page text until the word target is reached,
then emit a chunk carrying its [start, end] page range for source references.
Writes one file per chunk to data/chunks/ and a resumable data/state.json.
"""
import json
import sys
from pathlib import Path

# Allow running as a script (`python pipeline/chunk.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.books import by_book

TEXT_DIR = Path("data/text")
CHUNK_DIR = Path("data/chunks")
STATE_FILE = Path("data/state.json")
TARGET_WORDS = 700


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


def load_previous_state() -> dict:
    """Previous chunk state, so `generated` flags survive a re-chunk."""
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("chunks", {})


def main() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    previous = load_previous_state()
    state = {"chunks": {}}
    drifted: list[str] = []
    for text_file in sorted(TEXT_DIR.glob("*.json")):
        data = json.loads(text_file.read_text(encoding="utf-8"))
        prefix = by_book(data["book"])["book_id"]
        for i, ch in enumerate(chunk_pages(data["pages"]), 1):
            cid = f"{prefix}-c{i:03d}"
            chunk = {"chunk_id": cid, "book": data["book"],
                     "pages": ch["pages"], "text": ch["text"]}
            (CHUNK_DIR / f"{cid}.json").write_text(
                json.dumps(chunk, ensure_ascii=False, indent=1), encoding="utf-8")
            prev = previous.get(cid, {})
            if prev and prev.get("pages") != ch["pages"]:
                drifted.append(cid)
            state["chunks"][cid] = {"book": data["book"], "pages": ch["pages"],
                                    "words": len(ch["text"].split()),
                                    "generated": prev.get("generated", False)}
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(state['chunks'])} chunks -> {CHUNK_DIR}")
    lost = sorted(cid for cid, v in previous.items()
                  if v.get("generated") and cid not in state["chunks"])
    if drifted:
        print(f"WARNING: {len(drifted)} chunk(s) changed page range: {drifted[:10]}")
    if lost:
        print(f"WARNING: {len(lost)} generated chunk(s) disappeared: {lost[:10]}")


if __name__ == "__main__":
    sys.exit(main())
