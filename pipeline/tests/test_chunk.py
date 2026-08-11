import unittest
from pipeline.chunk import chunk_pages
from pipeline.books import lookup, by_book


class TestBookRegistry(unittest.TestCase):
    def test_resolves_every_source_filename(self):
        cases = {
            "Tom1. Mansur Rahnama.pdf": "t1",
            "Tom2. Mansur Rahnama.pdf": "t2",
            "Tom3. Mansur Rahnama.pdf": "t3",
            "Sormatologia zachowawcza z endodoncją- Jańczuk 2014.pdf": "jz",
            "Arabska_ocr.pdf": "ae",
        }
        for filename, book_id in cases.items():
            self.assertEqual(lookup(filename)["book_id"], book_id, filename)

    def test_ignored_source_returns_none(self):
        name = "Arabska_Przedpełska_B,_Pawlicka_H_Współczesna_endodoncja_w_praktyce.pdf"
        self.assertIsNone(lookup(name))

    def test_unknown_filename_raises(self):
        with self.assertRaises(KeyError):
            lookup("Jakas_nowa_ksiazka.pdf")

    def test_by_book_maps_stored_book_name(self):
        self.assertEqual(by_book("Tom2")["book_id"], "t2")
        with self.assertRaises(KeyError):
            by_book("Tom9")


class TestChunkPages(unittest.TestCase):
    def test_short_book_one_chunk(self):
        pages = [{"page": 1, "text": "krótki tekst"}]
        chunks = chunk_pages(pages, target_words=700)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["pages"], [1, 1])

    def test_splits_on_word_target(self):
        pages = [{"page": p, "text": "słowo " * 100} for p in range(1, 6)]
        chunks = chunk_pages(pages, target_words=150)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c["text"].strip() for c in chunks))

    def test_page_range_tracks_consecutive_pages(self):
        pages = [{"page": p, "text": "słowo " * 80} for p in range(3, 7)]
        chunks = chunk_pages(pages, target_words=150)
        # first chunk should start at page 3 and span >=1 page
        self.assertEqual(chunks[0]["pages"][0], 3)
        self.assertLessEqual(chunks[0]["pages"][0], chunks[0]["pages"][1])

    def test_skips_empty_pages(self):
        pages = [{"page": 1, "text": ""}, {"page": 2, "text": "tekst tu"}]
        chunks = chunk_pages(pages, target_words=700)
        self.assertEqual(chunks[0]["pages"], [2, 2])
