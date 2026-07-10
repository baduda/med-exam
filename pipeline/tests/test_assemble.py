import json
import tempfile
import unittest
from pathlib import Path

from pipeline.assemble import load_bank, balance_options


def good():
    return {"id": "t2-c016-001",
            "source": {"book": "Tom2", "pages": [42, 43]}, "question": "P?",
            "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            "correct": "C", "explanation": "bo tak"}


class TestLoadBank(unittest.TestCase):
    def test_loads_and_flattens(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "a.json").write_text(json.dumps([good()]), encoding="utf-8")
            Path(d, "b.json").write_text(json.dumps([good(), good()]), encoding="utf-8")
            self.assertEqual(len(load_bank(Path(d))), 3)

    def test_empty_dir_gives_empty_bank(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_bank(Path(d)), [])


class TestBalanceOptions(unittest.TestCase):
    def test_preserves_correct_answer_text(self):
        q = good()
        correct_text = q["options"][q["correct"]]
        b = balance_options(q)
        self.assertEqual(b["options"][b["correct"]], correct_text)

    def test_preserves_all_option_texts(self):
        q = good()
        b = balance_options(q)
        self.assertEqual(sorted(b["options"].values()), sorted(q["options"].values()))

    def test_deterministic(self):
        q = good()
        self.assertEqual(balance_options(q), balance_options(q))

    def test_does_not_mutate_input(self):
        q = good()
        original = dict(q["options"])
        balance_options(q)
        self.assertEqual(q["options"], original)

    def test_spreads_positions_across_ids(self):
        # different ids should not all land the correct answer on the same key
        positions = set()
        for i in range(30):
            q = good(); q["id"] = f"t2-c001-{i:03d}"
            positions.add(balance_options(q)["correct"])
        self.assertGreater(len(positions), 1)
