import unittest
from pipeline.extract import dehyphenate, split_chapters

class TestDehyphenate(unittest.TestCase):
    def test_joins_linebreak_hyphen(self):
        self.assertEqual(dehyphenate("szczę-\nkowy"), "szczękowy")

    def test_keeps_normal_newline_as_space(self):
        self.assertEqual(dehyphenate("ala\nma kota"), "ala ma kota")

class TestSplitChapters(unittest.TestCase):
    def test_splits_on_heading(self):
        pages = [
            {"page": 1, "text": "9. Zatoki szczękowe\nWstęp tekst"},
            {"page": 2, "text": "dalszy tekst"},
            {"page": 3, "text": "10. Urazy\nkolejny tekst"},
        ]
        chs = split_chapters(pages)
        self.assertEqual([c["chapter"] for c in chs], ["9", "10"])
        self.assertEqual(chs[0]["pages"], [1, 2])
        self.assertIn("Wstęp", chs[0]["text"])
