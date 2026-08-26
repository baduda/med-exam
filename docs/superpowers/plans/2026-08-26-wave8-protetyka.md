# Wave 8 — protetyka: Majewski (`mj`) and Dejak (`dj`)

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a fourth domain — protetyka — with two books that both carry a usable
text layer, so neither needs the OCR path (wave 7) nor the vision path (wave 6).
Majewski is the systematic textbook; Dejak is the procedural vademecum.

**Target:** whatever the chunks support at the protocol's 2–3 questions per chunk.
No quota — the numbers below are estimates, never a floor (see wave 6).

## Source inventory (measured 2026-08-26)

| File | `book_id` | PDF pages | Book pages | Embedded text | Garble |
|---|---|---|---|---|---|
| `OCR Majewski - Współczesna protetyka stomatologiczna.pdf` | `mj` | 438 | 438 (1:1) | 205 380 words | **0.09%** |
| `Vademecum_wykonywania_protez_staA_ych_i_ruchomych_Beata_Dejak.pdf` | `dj` | 197 spreads | 392 | 80 047 words | **1.27%** |

Both pass the <2% garble gate, measured on 5–6 sampled pages each after the soft-hyphen
fix below. Existing bank: 3534 Q, 1243 chunks.

New identifiers (fixed, stable forever):

- `book_id` = `mj` · `source.book` = `Majewski` · label `Majewski — protetyka stomatologiczna`
- `book_id` = `dj` · `source.book` = `Dejak` · label `Dejak — vademecum protetyczne`
- domain = `protetyka` for both

## Global constraints (unchanged)

- Content Polish; code/docs/JSON keys English.
- 5 options A–E, exactly one correct; `assemble.py` randomises the correct position.
- `source.pages` must come from the chunk. Never invented.
- Generation is agent-in-session (no API key), resumable via `data/state.json`.
- Generation agents never touch `state.json`, `assemble.py`, or `git`.

---

## Phase 1 — ingestion (mechanical)

- [ ] `pipeline/books.py`: register both PDFs. `mj` is an ordinary `text` book;
      `dj` is `"mode": "spread"` (see phase 2).
- [ ] `pipeline/extract.py`: `dehyphenate()` must drop the **soft hyphen** (U+00AD).
      Majewski's OCR marks every line-break hyphenation with `\xad` instead of `-`,
      which reads as 5.1% garbled tokens until joined; the real rate is 0.09%. No
      existing book contains a single U+00AD, so the change is a no-op for them.
- [ ] `pipeline/tests/test_extract.py`: cover `\xad` joining and the spread paging.
- [ ] `docs/app.js`: one `BOOKS` row per book.
- [ ] `python pipeline/extract.py && python pipeline/chunk.py`.

## Phase 2 — Dejak is a spread PDF (decided, not deferred)

One PDF page holds two facing printed pages, rotated 90°. Unlike the wave-7 scan, the
numbering **is** a formula, verified at pdf 4→6, 11→20, 51→100, 151→300, 197→392:

    printed_left = 2 * pdf_page - 2

The page is **not** split geometrically. A midpoint clip cuts words in half
(`powierzchnia` → `owierzchnia`) because the gutter is not centred and the page is
rotated; a block-clustering split is real work for ±1 page of precision. Instead each
spread is emitted as one record numbered with its **left printed page**, so a citation
names the spread that carries the text. Recorded in AGENTS.md.

Because the text layer is native (not OCR), reading order across the spread is the
publisher's own and stays coherent — no reflow work needed.

## Phase 3 — Majewski page references

The OCR dropped every running head, so no printed page number survives in the text
layer. `source.pages` therefore carries **PDF page numbers**, which is what every other
`text` book in the bank already does. Body starts at pdf 21; pdf 1–20 are the title,
the publisher block and the author's own publication list.

## Phase 4 — generation waves

~280 chunks for `mj`, ~114 for `dj`. Process ~18–20 chunks per run.

Skip aggressively (GENERATION.md rule 2), these books are full of it:

- Majewski pdf 1–20 (author's monograph list — pure trivia) and pdf 431–438 (skorowidz).
- Chapter-tail `Piśmiennictwo` blocks in both.
- Historical/institutional prose: Majewski opens several chapters with department
  history and named professors. If the answer is a person, a city or a year, skip.
- Dejak's laboratory step-lists are prose but often pure sequence recitation; keep only
  where the chunk states a *reason* or a *criterion* a candidate could be examined on.

After each wave: `mark_generated.py` → `build_core.py` → `assemble.py` → commit.

## Estimate (measured after chunking, 2026-08-26)

`chunk.py` fills a chunk with *whole pages* until it passes 700 words, so with these
books' ~480-word pages a chunk lands near 1000 words — the count is words/~1000, not
words/700. Actual chunk counts:

| Book | words | chunks | avg words/chunk | after ~10-12% junk skip | x 2.7 Q/chunk |
|---|---|---|---|---|---|
| Majewski | 195 079 | 187 | 1043 | ~165 | **~445** (400-500) |
| Dejak | 77 957 | 84 | 928 | ~74 | **~200** (180-220) |

The 2.7 rate is what the three most recent books actually produced (Arabska 2.67,
Górska 2.72, GorskaLDEK 2.81); the older Tom2/Tom3 waves ran at 3.6 under a different
protocol and are not the baseline.

Bank 3534 -> **~4180**.

## Phase 1 result (done 2026-08-26)

- [x] both books registered in `books.py`; `mj` text, `dj` spread
- [x] soft-hyphen fix in `dehyphenate()` — Majewski garble 5.1% -> 0.09%
- [x] `extract_spread_book()` + tests (39 tests pass)
- [x] `docs/app.js` rows added
- [x] `extract.py`: Majewski 430/438 pages with text; Dejak 197 spreads -> printed 1-393
- [x] `chunk.py`: 1514 chunks total, `mj-c001..c187`, `dj-c001..c084`, no page drift
