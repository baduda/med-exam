import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import fitz

from pipeline import scan


class TestHalves(unittest.TestCase):
    def test_splits_a_spread_down_the_middle(self):
        doc = fitz.open()
        page = doc.new_page(width=800, height=500)
        left, right = scan.halves(page)
        self.assertEqual((left.x0, left.x1), (0, 400))
        self.assertEqual((right.x0, right.x1), (400, 800))
        self.assertEqual((left.y0, left.y1), (0, 500))


class TestPagemap(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        patcher = mock.patch.object(scan, "PAGEMAP_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, spreads):
        (self.dir / "xx.json").write_text(json.dumps({"spreads": spreads}), encoding="utf-8")

    def test_keys_become_ints(self):
        self.write({"5": 2, "6": 4})
        self.assertEqual(scan.load_pagemap("xx"), {5: 2, 6: 4})

    def test_missing_spreads_are_simply_absent(self):
        """Duplicate photos and front matter are left out of the map, so the
        pages they would carry never reach data/text."""
        self.write({"5": 2, "7": 6})
        self.assertNotIn(6, scan.load_pagemap("xx"))


class TestRealPagemap(unittest.TestCase):
    def test_pl_pagemap_gives_every_page_exactly_once(self):
        pagemap = scan.load_pagemap("pl")
        pages = [p for first in pagemap.values() for p in (first, first + 1)]
        self.assertEqual(len(pages), len(set(pages)), "a page number is claimed twice")
        self.assertEqual(min(pages), 2)
        self.assertEqual(max(pages), 232)


if __name__ == "__main__":
    unittest.main()


class TestRenderPreservesTranscriptions(unittest.TestCase):
    """extract.py used to reset every page of an image book to "", wiping
    transcriptions that only exist there. Regression guard."""

    def test_existing_text_is_carried_forward(self):
        from pipeline import extract
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "Book.json").write_text(json.dumps({"book": "Book", "pages": [
                {"page": 1, "text": "przyzębie", "image": "x.jpg"},
                {"page": 2, "text": "", "image": "y.jpg"},
            ]}), encoding="utf-8")
            with mock.patch.object(extract, "OUT_DIR", out):
                self.assertEqual(extract.existing_text("Book"), {1: "przyzębie", 2: ""})
                self.assertEqual(extract.existing_text("Missing"), {})
