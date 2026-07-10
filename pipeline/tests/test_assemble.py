import json
import tempfile
import unittest
from pathlib import Path

from pipeline.assemble import load_bank


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
