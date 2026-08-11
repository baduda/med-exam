"""Mark a range of chunks as generated in data/state.json.

Generation agents must not write state.json concurrently, so the orchestrator
marks a whole wave's range at once after the agents finish. A chunk that was
deliberately skipped as junk is marked too — it is done, not pending.

    python pipeline/mark_generated.py t1-c001 t1-c216
"""
import json
import sys
from pathlib import Path

STATE_FILE = Path("data/state.json")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    first, last = argv
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    in_range = sorted(cid for cid in state["chunks"] if first <= cid <= last)
    if not in_range:
        print(f"no chunks between {first} and {last}")
        return 1
    newly = [cid for cid in in_range if not state["chunks"][cid]["generated"]]
    for cid in in_range:
        state["chunks"][cid]["generated"] = True
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"marked {len(newly)} new of {len(in_range)} chunks in {first}..{last}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
