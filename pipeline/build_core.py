"""Rebuild data/core.json — the "Kluczowe (LDEK)" subset of the bank.

The subset is the smaller, higher-yield set a candidate practises first. Two
sources feed it:

- **Existing entries are preserved.** The Tom2/Tom3 core was hand-ranked for
  CEM relevance; that judgement is not reproducible from the text, so ids
  already listed are kept as long as the question still exists.
- **New books are selected by rule.** Every `combined` and `clinical` question
  is included (they test reasoning rather than recall), plus one question from
  any chunk that would otherwise be unrepresented, so no part of a book is
  missing from the core scope.

Re-run after each generation wave; it is idempotent and only ever grows the
subset for books it has not covered yet.

    python pipeline/build_core.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

BANK = Path("data/questions.json")
CORE_FILE = Path("data/core.json")


def chunk_of(question_id: str) -> str:
    """'jz-c100-002' -> 'jz-c100'."""
    return question_id.rsplit("-", 1)[0]


def select(bank: list[dict], keep: set[str]) -> set[str]:
    """Return the core id set: `keep` (still-valid prior picks) plus rule-based
    picks for every book that has no prior picks at all."""
    core = {q["id"] for q in bank if q["id"] in keep}
    covered_books = {q["source"]["book"] for q in bank if q["id"] in core}

    fresh = [q for q in bank if q["source"]["book"] not in covered_books]
    core |= {q["id"] for q in fresh if q.get("type") in ("combined", "clinical")}

    represented = {chunk_of(qid) for qid in core}
    for q in sorted(fresh, key=lambda q: q["id"]):
        if chunk_of(q["id"]) not in represented:
            core.add(q["id"])
            represented.add(chunk_of(q["id"]))
    return core


def main() -> int:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    previous = set(json.loads(CORE_FILE.read_text(encoding="utf-8"))) if CORE_FILE.exists() else set()
    core = select(bank, previous)

    dropped = previous - core
    CORE_FILE.write_text(json.dumps(sorted(core), ensure_ascii=False, indent=1), encoding="utf-8")

    by_book = Counter(q["source"]["book"] for q in bank if q["id"] in core)
    total = Counter(q["source"]["book"] for q in bank)
    print(f"core: {len(core)} of {len(bank)} questions -> {CORE_FILE}")
    for book in sorted(total):
        print(f"  {book:<9} {by_book[book]:>4} / {total[book]:>4}")
    if dropped:
        print(f"dropped {len(dropped)} id(s) no longer in the bank: {sorted(dropped)[:10]}")
    missing = sorted(b for b in total if not by_book[b])
    if missing:
        print(f"WARNING: no core questions for {missing}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
