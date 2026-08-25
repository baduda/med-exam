# Wave 7 — seventh book: Periodontologia. Podręcznik dla studentów i do LDEK (Górska 2022)

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a seventh source book to the bank with ordinary recognition (OCR), not the
vision path built for the 2013 Periodontologia. The source is the current LDEK textbook,
so its yield matters more per page than any book so far.

**Target:** whatever the chunks support at the protocol's 2–3 questions per chunk.
No quota — the plan's number is an estimate, never a floor (see wave 6).

## Source inventory (measured 2026-08-25)

| File | `book_id` | PDF pages | Book pages | Embedded text |
|---|---|---|---|---|
| `Perio Górska 2022.pdf` | `pl` | 116 spreads | 232 | **0 words** |

Existing bank: 3259 Q (Tom2 863, Janczuk 571, Tom1 543, Tom3 457, Gorska 433,
Arabska 392), 1145 chunks, 1390 flagged `core: true`.

New identifiers (fixed, stable forever):

- `book_id` = `pl` · `source.book` = `GorskaLDEK`
- label = `Górska — periodontologia (LDEK 2022)` · domain = `periodontologia`

## Global constraints (unchanged)

- Content Polish; code/docs/JSON keys English.
- 5 options A–E, exactly one correct; `assemble.py` randomises the correct position.
- `source.pages` must come from the chunk. Never invented.
- Generation is agent-in-session (no API key), resumable via `data/state.json`.
- `books/`, `data/chunks/`, `data/questions/`, `data/images/`, `data/transcripts/` gitignored.
  `data/pagemap/` **is** committed — it is hand-verified input, not an intermediate.
- Generation agents never touch `state.json`, `assemble.py`, or `git`.

---

## Phase 1 — OCR accepted on measurement (done 2026-08-25)

Unlike the 2013 book, this one passes the gate. Measured on an 8-half-page sample
(book pages 41–42, 119–120, 179–180, 219–220) against a 81 503-word vocabulary built
from the five existing text books, after de-hyphenation:

| Metric | Value |
|---|---|
| raw out-of-vocabulary | 8.78% |
| of which real Polish/English words absent from the other books | ~8.4% (`rezolwiny`, `protektyny`, `alendronowy`, bibliography surnames) |
| **actual garble** | **~0.4%** (12 tokens of 2837) |
| gate | < 2% |

Two findings that shaped `scan.py`:

- [x] **ocrmypdf loses text; direct tesseract does not.** `ocrmypdf --force-ocr` dropped
      whole spans of body text (`w wyniku ___ przez pacjenta`) and mangled coloured
      headings and table cells. `tesseract -l pol --psm 3` on a 400 dpi render of the
      same half-page recovered every one of them. The pipeline shells out to tesseract.
- [x] **Do not binarize the body.** Binarizing to make the white-on-red page numbers
      readable costs real text — `250 200 mg` for `250–500 mg`, `7 14 dm` for `7–14 dni`.
      Body OCR renders plain grayscale; page numbers come from the map instead.

## Phase 2 — spread splitting and the page map (done 2026-08-25)

The PDF holds one image per *spread*, so a PDF page carries two book pages, and the
printed page numbers do not follow any formula: the scan mixes true spreads
(verso|recto) with misaligned captures (recto|verso), duplicates spreads 12 and 95, and
drops others. Three successive attempts to infer the numbering (red-box OCR, header-band
OCR, DP over anchors) all left ambiguity, so the map was read off the 116 header bands
by eye and frozen.

- [x] `data/pagemap/pl.json` — 110 spreads → left page number; right is +1.
- [x] Coverage **220 of 232 pages**. Absent from the scan and therefore from the bank:
      1, 8, 27, 36, 37, 38, 67, 92, 125, 190, 199, 210.
- [x] Spreads 1–4 (cover, copyright, spis treści) and duplicate spreads 12, 95 are
      deliberately not in the map.

## Phase 3 — pipeline changes (done 2026-08-25)

- [x] `pipeline/books.py` — third mode `"scan"`; entry for `pl`. Pattern
      `Perio Górska*.pdf` does not collide with `Periodontologia*.pdf` (`pd`).
- [x] `pipeline/scan.py` — new. Splits spreads, renders halves at 400 dpi (cached under
      `data/images/pl/`), OCRs each, emits the usual `{"book", "pages"}` shape keyed by
      real book page numbers.
- [x] `pipeline/extract.py` — branches on `mode(entry) == "scan"`.
- [x] Tests: `pipeline/tests/test_scan.py` (halving, page map loading, and a check that
      the real `pl` map claims every page exactly once); registry cases in
      `test_chunk.py`. 34 tests pass.
- [x] `docs/app.js` — book row. `AGENTS.md` — table, layout, the two traps above.

## Phase 4 — extract and chunk (done 2026-08-25)

- [x] `python pipeline/extract.py` — 220 pages, 93 812 words, no empty page.
- [x] Regression gate: 0 chunks lost, 0 page-range drift, 0 `generated` flags lost;
      the only additions are the 98 `pl-*` chunks. 1145 → 1243 chunks.
- [x] **Bug found and fixed while re-running.** `extract.py` rebuilt the *2013*
      Periodontologia from images and reset every page to `""`, wiping the 130 686
      words of wave-6 vision transcription — the only copy of that text. Restored from
      git, `render_book` now carries existing text forward (`existing_text()`), and
      `test_scan.py` guards it.
- [x] `scan.py` now caches Tesseract output beside each page image; without it a
      re-run of `extract.py` cost ~30 min of CPU to reproduce a file it already had.

## Phase 5 — generation (done 2026-08-25)

- [x] One wave of 8 parallel Sonnet subagents covered all 98 chunks.
- [x] 92 chunks yielded questions; 6 were skipped as pure numbered `PIŚMIENNICTWO`
      lists: `pl-c012`, `pl-c052`, `pl-c053`, `pl-c074`, `pl-c087`, `pl-c096`.
- [x] `python pipeline/mark_generated.py pl-c001 pl-c098` — 98 chunks marked by the
      orchestrator, skipped ones included (they are done, not pending).

## Phase 6 — build and verify (done 2026-08-25)

**Outcome: 275 questions.** Bank 3259 → **3534**; core 1390 → 1483.

| Book | Questions | Core |
|---|---|---|
| Tom2 | 863 | 418 |
| Janczuk | 571 | 228 |
| Tom1 | 543 | 264 |
| Tom3 | 457 | 182 |
| Gorska | 433 | 140 |
| Arabska | 392 | 158 |
| **GorskaLDEK** | **275** | **93** |

- [x] `build_core.py` then `assemble.py` — OK, 3534 questions.
- [x] Verified: 3534 unique ids; 0 malformed option sets; every `pl` `source.pages`
      inside 2–232 and none from the 12 absent pages; answer keys A 47 / B 52 / C 61 /
      D 57 / E 58; 249 plain, 14 combined, 12 clinical; `docs/questions.json` identical.
- [x] Spot-checked `pl-c019-001` (BoP > 10% gingivitis threshold) and `pl-c050-002`
      (SDD doxycycline inhibits MMPs) verbatim against their chunk text.
- [x] 35 tests pass; local server smoke test serves 3534 questions.
- [x] Commit and push.

## Known defect — four page labels are low by one

Chapter openers print their page number at the **bottom** of the page, not in the
header band the map was read from, and the blank verso facing an opener was not
photographed. So on the four spreads whose right half is a chapter opener, the two
halves are not consecutive pages, and the map's "right = left + 1" rule labels the
opener one too low:

| Spread | Labelled | Actually | Blank verso not in the scan |
|---|---|---|---|
| 17 | 25 \| 26 | 25 \| **27** | 26 |
| 35 | 65 \| 66 | 65 \| **67** | 66 |
| 63 | 123 \| 124 | 123 \| **125** | 124 |
| 100 | 197 \| 198 | 197 \| **199** | 198 |

Nine questions cite the low number — `pl-c013-001..003` (s. 25–26 → 25–27),
`pl-c030-001..003` (s. 63–66 → 63–67), `pl-c079-001..003` (s. 198–200 → 199–200).
Their content and answer keys are correct; only the printed citation is off by one.
Left as-is by the user's decision on 2026-08-25.

**To fix:** give `data/pagemap/pl.json` an explicit right page for those four spreads
(the loader currently derives it as left + 1), re-run `extract.py` (OCR is cached, so
this is fast), re-chunk, and remap `source.pages` in the affected `data/questions/pl-*`
files. Chunk grouping does not change — only the recorded ranges — so chunk and
question ids stay stable.

The other eight absent pages are genuine and harmless: 8, 92, 190 and 210 are blank
versos facing chapter openers; 36–38 are the tail of chapter 3's bibliography, simply
not photographed.
