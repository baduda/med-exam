import unittest
from pipeline.chunk import chunk_pages, book_prefix


class TestBookPrefix(unittest.TestCase):
    def test_extracts_volume_number(self):
        self.assertEqual(book_prefix("Tom2"), "t2")
        self.assertEqual(book_prefix("Tom3"), "t3")


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
