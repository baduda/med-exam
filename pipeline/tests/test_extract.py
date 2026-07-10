import unittest
from pipeline.extract import dehyphenate

class TestDehyphenate(unittest.TestCase):
    def test_joins_linebreak_hyphen(self):
        self.assertEqual(dehyphenate("szczę-\nkowy"), "szczękowy")

    def test_keeps_normal_newline_as_space(self):
        self.assertEqual(dehyphenate("ala\nma kota"), "ala ma kota")

    def test_collapses_whitespace(self):
        self.assertEqual(dehyphenate("a   b\n\nc"), "a b c")
