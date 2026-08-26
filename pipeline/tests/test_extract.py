import unittest
from unittest.mock import patch

from pipeline.extract import dehyphenate, extract_spread_book


class TestDehyphenate(unittest.TestCase):
    def test_joins_linebreak_hyphen(self):
        self.assertEqual(dehyphenate("szczę-\nkowy"), "szczękowy")

    def test_joins_soft_hyphen_at_linebreak(self):
        self.assertEqual(dehyphenate("kształ\u00ad\ntowanie"), "kształtowanie")

    def test_drops_midline_soft_hyphen(self):
        self.assertEqual(dehyphenate("czyn\u00adność"), "czynność")

    def test_keeps_normal_newline_as_space(self):
        self.assertEqual(dehyphenate("ala\nma kota"), "ala ma kota")

    def test_collapses_whitespace(self):
        self.assertEqual(dehyphenate("a   b\n\nc"), "a b c")


class FakePage:
    def __init__(self, text):
        self.text = text

    def get_text(self):
        return self.text


class FakeDoc:
    def __init__(self, texts):
        self.pages = [FakePage(t) for t in texts]
        self.page_count = len(texts)

    def __getitem__(self, i):
        return self.pages[i]


class TestExtractSpreadBook(unittest.TestCase):
    def test_numbers_spreads_with_left_printed_page(self):
        doc = FakeDoc(["tytuł", "autorzy", "spis", "rozdział 4"])
        with patch("pipeline.extract.fitz.open", return_value=doc):
            data = extract_spread_book("x.pdf", "Dejak")
        # pdf 1 has no printed number of its own; pdf 4 prints 6.
        self.assertEqual([p["page"] for p in data["pages"]], [1, 2, 4, 6])
        self.assertEqual(data["book"], "Dejak")

    def test_dehyphenates_spread_text(self):
        with patch("pipeline.extract.fitz.open", return_value=FakeDoc(["szczę-\nkowy"])):
            data = extract_spread_book("x.pdf", "Dejak")
        self.assertEqual(data["pages"][0]["text"], "szczękowy")
