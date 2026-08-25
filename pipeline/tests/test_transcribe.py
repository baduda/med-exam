import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import transcribe


class TestMergeBook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.text_dir = root / "text"
        self.transcript_dir = root / "transcripts"
        (self.transcript_dir / "pd").mkdir(parents=True)
        self.text_dir.mkdir()
        (self.text_dir / "Gorska.json").write_text(json.dumps({
            "book": "Gorska",
            "pages": [{"page": 1, "text": "stary tekst", "image": "a.jpg"},
                      {"page": 2, "text": "", "image": "b.jpg"}],
        }, ensure_ascii=False), encoding="utf-8")
        self.patches = [mock.patch.object(transcribe, "TEXT_DIR", self.text_dir),
                        mock.patch.object(transcribe, "TRANSCRIPT_DIR", self.transcript_dir)]
        for p in self.patches:
            p.start()
        self.entry = {"book_id": "pd", "book": "Gorska"}

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def write_transcript(self, name, pages):
        (self.transcript_dir / "pd" / name).write_text(
            json.dumps({"pages": pages}, ensure_ascii=False), encoding="utf-8")

    def test_fills_only_empty_pages(self):
        self.write_transcript("a.json", [{"page": 1, "text": "nowy"},
                                         {"page": 2, "text": "przyzębie"}])
        filled, skipped = transcribe.merge_book(self.entry, force=False)
        self.assertEqual((filled, skipped), (1, 1))
        pages = transcribe.load_pages("Gorska")["pages"]
        self.assertEqual(pages[0]["text"], "stary tekst")   # untouched
        self.assertEqual(pages[1]["text"], "przyzębie")

    def test_force_overwrites(self):
        self.write_transcript("a.json", [{"page": 1, "text": "nowy"}])
        filled, skipped = transcribe.merge_book(self.entry, force=True)
        self.assertEqual((filled, skipped), (1, 0))
        self.assertEqual(transcribe.load_pages("Gorska")["pages"][0]["text"], "nowy")

    def test_unknown_page_raises(self):
        self.write_transcript("a.json", [{"page": 99, "text": "x"}])
        with self.assertRaises(KeyError):
            transcribe.merge_book(self.entry, force=False)

    def test_missing_pages_lists_untranscribed(self):
        self.assertEqual(transcribe.missing_pages(transcribe.load_pages("Gorska")), [2])


if __name__ == "__main__":
    unittest.main()
