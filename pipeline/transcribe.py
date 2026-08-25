"""Merge agent transcriptions of page images into data/text/<Book>.json.

Books declared `mode: "image"` in books.py have no text layer and cannot be
OCR'd (the Periodontologia source is 96 dpi phone photos; Tesseract returns
~20% garbled tokens against a <2% gate). `extract.py` renders their pages to
data/images/<book_id>/pNNN.jpg with an empty "text" per page; agents read those
images and write transcriptions to data/transcripts/<book_id>/*.json, which this
script merges back into the per-page text file. Once merged, the book is a
normal text book: chunk.py, assemble.py and build_core.py need no special case.

Transcription files are `{"pages": [{"page": 120, "text": "..."}, ...]}` — the
shape the generating agents are told to write. Merging is idempotent and
resumable: a page that already has text is left alone unless --force is given,
so a re-run only fills the gaps.

    python pipeline/transcribe.py status              # coverage report
    python pipeline/transcribe.py plan 12             # next page batches to hand out
    python pipeline/transcribe.py merge [--force]     # transcripts -> data/text
"""
import json
import sys
from pathlib import Path

# Allow running as a script (`python pipeline/transcribe.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.books import BOOKS, mode

TEXT_DIR = Path("data/text")
TRANSCRIPT_DIR = Path("data/transcripts")


def image_books() -> list[dict]:
    return [b for b in BOOKS if mode(b) == "image"]


def load_pages(book: str) -> dict:
    return json.loads((TEXT_DIR / f"{book}.json").read_text(encoding="utf-8"))


def missing_pages(data: dict) -> list[int]:
    """Pages that still have no transcription."""
    return [p["page"] for p in data["pages"] if not p["text"].strip()]


def cmd_status() -> int:
    for entry in image_books():
        data = load_pages(entry["book"])
        total = len(data["pages"])
        missing = missing_pages(data)
        words = sum(len(p["text"].split()) for p in data["pages"])
        print(f"{entry['book']}: {total - len(missing)}/{total} pages transcribed, "
              f"{words} words, {len(missing)} missing")
        if missing:
            print(f"  first missing: {missing[:15]}")
    return 0


def cmd_plan(batch_size: int) -> int:
    """Print the still-missing pages grouped into batches, one line per batch."""
    for entry in image_books():
        data = load_pages(entry["book"])
        missing = missing_pages(data)
        for i in range(0, len(missing), batch_size):
            batch = missing[i:i + batch_size]
            print(f"{entry['book_id']} {batch[0]}-{batch[-1]}: "
                  + " ".join(str(p) for p in batch))
    return 0


def merge_book(entry: dict, force: bool) -> tuple[int, int]:
    """Apply every transcript file for one book. Returns (filled, skipped)."""
    data = load_pages(entry["book"])
    by_page = {p["page"]: p for p in data["pages"]}
    filled = skipped = 0
    src_dir = TRANSCRIPT_DIR / entry["book_id"]
    for src in sorted(src_dir.glob("*.json")) if src_dir.exists() else []:
        payload = json.loads(src.read_text(encoding="utf-8"))
        for page in payload["pages"]:
            n, text = page["page"], page["text"].strip()
            if n not in by_page:
                raise KeyError(f"{src}: page {n} is not in {entry['book']}.json")
            if by_page[n]["text"].strip() and not force:
                skipped += 1
                continue
            by_page[n]["text"] = text
            filled += 1
    (TEXT_DIR / f"{entry['book']}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return filled, skipped


def cmd_merge(force: bool) -> int:
    for entry in image_books():
        filled, skipped = merge_book(entry, force)
        data = load_pages(entry["book"])
        missing = missing_pages(data)
        print(f"{entry['book']}: filled {filled} pages, kept {skipped} existing, "
              f"{len(missing)} still missing")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "status":
        return cmd_status()
    if cmd == "plan":
        return cmd_plan(int(rest[0]) if rest else 12)
    if cmd == "merge":
        return cmd_merge("--force" in rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
