"""Rebuild data/core.json — the "Kluczowe (LDEK)" subset of the bank.

The subset is the smaller, higher-yield set a candidate practises first. It has
two parts:

- `data/core_curated.json` — the original Tom2/Tom3 picks, hand-ranked for CEM
  relevance. That judgement cannot be re-derived from the text, so the file is
  frozen input: this script only ever reads it.
- Everything else is selected by rule: every `combined` and `clinical` question
  (they test reasoning rather than recall), plus one question from any chunk
  that would otherwise be unrepresented, so no part of a book is missing from
  the core scope.

Reads the per-chunk sources under `data/questions/`, NOT the built
`data/questions.json` — so it can run before or after `assemble.py` and still
see every question. Re-run after each generation wave; it is idempotent.

    python pipeline/build_core.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

# Allow running as a script (`python pipeline/build_core.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.assemble import load_bank

Q_DIR = Path("data/questions")
CURATED_FILE = Path("data/core_curated.json")
CORE_FILE = Path("data/core.json")


def chunk_of(question_id: str) -> str:
    """'jz-c100-002' -> 'jz-c100'."""
    return question_id.rsplit("-", 1)[0]


def select(bank: list[dict], curated: set[str]) -> set[str]:
    """Curated picks that still exist, plus rule-based picks for every book the
    curated set does not cover."""
    core = {q["id"] for q in bank if q["id"] in curated}
    curated_books = {q["source"]["book"] for q in bank if q["id"] in core}

    rest = [q for q in bank if q["source"]["book"] not in curated_books]
    core |= {q["id"] for q in rest if q.get("type") in ("combined", "clinical")}

    represented = {chunk_of(qid) for qid in core}
    for q in sorted(rest, key=lambda q: q["id"]):
        if chunk_of(q["id"]) not in represented:
            core.add(q["id"])
            represented.add(chunk_of(q["id"]))
    return core


def main() -> int:
    bank = load_bank(Q_DIR)
    curated = set(json.loads(CURATED_FILE.read_text(encoding="utf-8"))) if CURATED_FILE.exists() else set()
    core = select(bank, curated)

    stale = sorted(curated - {q["id"] for q in bank})
    CORE_FILE.write_text(json.dumps(sorted(core), ensure_ascii=False, indent=1), encoding="utf-8")

    by_book = Counter(q["source"]["book"] for q in bank if q["id"] in core)
    total = Counter(q["source"]["book"] for q in bank)
    print(f"core: {len(core)} of {len(bank)} questions -> {CORE_FILE}")
    for book in sorted(total):
        print(f"  {book:<9} {by_book[book]:>4} / {total[book]:>4}")
    if stale:
        print(f"WARNING: {len(stale)} curated id(s) no longer in the bank: {stale[:10]}")
    missing = sorted(b for b in total if not by_book[b])
    if missing:
        print(f"WARNING: no core questions for {missing}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
