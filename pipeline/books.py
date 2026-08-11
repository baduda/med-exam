"""Registry of source books.

Book ids used to be derived from digits in the filename ("Tom2" -> "t2"), which
only works for the numbered Rahnama volumes. Non-numbered titles need an
explicit mapping, so every source PDF is declared here instead of guessed.

- `pattern`  — glob matched against the PDF filename in books/.
- `book_id`  — chunk/question id prefix. Stable forever: existing question ids
               reference it.
- `book`     — value stored in `source.book` of every question.
- `label`    — Polish display name for the web app's book filter.
- `domain`   — broad exam area, used to group books in the UI.
"""
import fnmatch
import unicodedata

BOOKS = (
    {"pattern": "Tom1.*.pdf", "book_id": "t1", "book": "Tom1",
     "label": "Rahnama, tom 1", "domain": "chirurgia"},
    {"pattern": "Tom2.*.pdf", "book_id": "t2", "book": "Tom2",
     "label": "Rahnama, tom 2", "domain": "chirurgia"},
    {"pattern": "Tom3.*.pdf", "book_id": "t3", "book": "Tom3",
     "label": "Rahnama, tom 3", "domain": "chirurgia"},
    {"pattern": "*Jańczuk*.pdf", "book_id": "jz", "book": "Janczuk",
     "label": "Jańczuk — stomatologia zachowawcza", "domain": "zachowawcza"},
    {"pattern": "Arabska_ocr.pdf", "book_id": "ae", "book": "Arabska",
     "label": "Arabska-Przedpełska — endodoncja", "domain": "zachowawcza"},
)

# Files in books/ that are deliberately not sources. The original Arabska PDF is
# an image-only scan superseded by Arabska_ocr.pdf (see AGENTS.md for the OCR step).
IGNORED = ("Arabska_Przedpełska*.pdf",)


def _matches(filename: str, pattern: str) -> bool:
    """Glob match that is blind to Unicode form — macOS filenames are NFD,
    the patterns in this file are NFC, so "Jańczuk" would not match itself."""
    nfc = lambda s: unicodedata.normalize("NFC", s)
    return fnmatch.fnmatch(nfc(filename), nfc(pattern))


def lookup(filename: str) -> dict | None:
    """Return the registry entry for a PDF filename, or None if it is ignored.

    Raises KeyError for a file that is neither registered nor explicitly ignored,
    so a newly dropped book is never silently chunked under a guessed id.
    """
    for entry in BOOKS:
        if _matches(filename, entry["pattern"]):
            return entry
    for pattern in IGNORED:
        if _matches(filename, pattern):
            return None
    raise KeyError(f"{filename}: not in pipeline/books.py registry")


def by_book(book: str) -> dict:
    """Return the registry entry whose `book` field matches (as stored in questions)."""
    for entry in BOOKS:
        if entry["book"] == book:
            return entry
    raise KeyError(f"{book}: unknown book name")
