"""Merge per-chunk question files into the validated final bank.

Reads every JSON list under data/questions/, validates the whole bank against
pipeline/schema.py, and writes data/questions.json plus a copy at
web/questions.json. Exits non-zero (printing errors) if anything is invalid.
"""
import hashlib
import json
import random
import sys
from pathlib import Path

# Allow running as a script (`python pipeline/assemble.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline.schema import OPTION_KEYS, validate_bank


def balance_options(q: dict) -> dict:
    """Deterministically shuffle a question's options so the correct answer's
    position is not biased (generators over-pick 'B'). Seeded by id → stable
    across rebuilds. Returns a new dict; input is not mutated."""
    correct_value = q["options"][q["correct"]]
    values = [q["options"][k] for k in OPTION_KEYS]
    seed = int(hashlib.md5(q["id"].encode("utf-8")).hexdigest(), 16)
    random.Random(seed).shuffle(values)
    new_options = dict(zip(OPTION_KEYS, values))
    new_correct = next(k for k in OPTION_KEYS if new_options[k] == correct_value)
    out = dict(q)
    out["options"] = new_options
    out["correct"] = new_correct
    return out

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
    bank = [balance_options(q) for q in load_bank(Q_DIR)]
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
