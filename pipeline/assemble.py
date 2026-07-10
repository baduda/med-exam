"""Merge per-chunk question files into the validated final bank.

Reads every JSON list under data/questions/, validates the whole bank against
pipeline/schema.py, and writes data/questions.json plus a copy at
web/questions.json. Exits non-zero (printing errors) if anything is invalid.
"""
import json
import sys
from pathlib import Path

from pipeline.schema import validate_bank

Q_DIR = Path("data/questions")
OUT = Path("data/questions.json")
WEB_COPY = Path("web/questions.json")


def load_bank(directory: Path) -> list[dict]:
    """Load and flatten every JSON list of questions in `directory`."""
    bank: list[dict] = []
    for f in sorted(directory.glob("*.json")):
        bank.extend(json.loads(f.read_text(encoding="utf-8")))
    return bank


def main() -> int:
    bank = load_bank(Q_DIR)
    errors = validate_bank(bank)
    if errors:
        print(f"{len(errors)} validation errors:")
        for e in errors[:50]:
            print("  -", e)
        return 1
    payload = json.dumps(bank, ensure_ascii=False, indent=1)
    OUT.write_text(payload, encoding="utf-8")
    WEB_COPY.parent.mkdir(parents=True, exist_ok=True)
    WEB_COPY.write_text(payload, encoding="utf-8")
    print(f"OK: {len(bank)} questions -> {OUT} and {WEB_COPY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
