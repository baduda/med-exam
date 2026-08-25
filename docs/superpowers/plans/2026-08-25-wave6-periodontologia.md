# Wave 6 — sixth book: Periodontologia (Górska & Konopka 2013)

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add a sixth source book and a third domain (`periodontologia`) to the bank,
taking it from 2826 questions to ~3400, without disturbing any existing id.

**Target:** 500–700 new questions (hard floor 400).

**Outcome: 405.** The book yielded 159 chunks, not the 190–290 the page count suggested,
and 20 of those are front matter, contents, `Piśmiennictwo` or index. At the protocol's
2–3 questions per chunk that caps the book near 400. A second pass over the same chunks
would add ~150 more; the user decided the 500 figure was not a requirement, so the wave
closed at one pass rather than padding the bank.

## Source inventory (measured 2026-08-25)

| File | `book_id` | Pages | Embedded text | Note |
|---|---|---|---|---|
| `Periodontologia_Współczesna_R_Górska,_T_Konopka_2013.pdf` | `pd` | 541 | **0 words / 541 empty pages** | phone photos, not a scan |

Existing bank: 2826 Q (Tom2 863, Janczuk 571, Tom1 543, Tom3 457, Arabska 392),
986 chunks, 1245 flagged `core: true`.

New identifiers (fixed, stable forever):

- `book_id` = `pd` · `source.book` = `Gorska` (ASCII, like `Janczuk`)
- label = `Górska — periodontologia` · domain = `periodontologia` (**new third domain**)

## Global constraints (unchanged)

- Content Polish; code/docs/JSON keys English.
- 5 options A–E, exactly one correct; `assemble.py` randomises the correct position.
- `source.pages` must come from the chunk. Never invented.
- Generation is agent-in-session (no API key), resumable via `data/state.json`.
- `books/`, `data/chunks/`, `data/questions/`, `data/images/`, `data/transcripts/` gitignored.
- Generation agents never touch `state.json`, `assemble.py`, or `git`.

---

## Phase 1 — OCR rejected on measurement (done 2026-08-25)

OCR was tried first and **failed the quality gate**; this section records why, so the
next person does not retry it.

| | Arabska (the OCR precedent) | Periodontologia |
|---|---|---|
| page image | 1163×1613 | **689×1024** (~96 dpi) |
| source | flatbed scan | **phone photos** — finger in frame, curved lines, uneven light |
| garbled tokens after OCR | 0.1% | **~20–23%** (gate: <2%) |

`ocrmypdf -l pol --force-ocr --deskew --oversample 400` fixed the top of a page and
left the bottom — where lines curve into the gutter — as noise (`oczyszbzi`, `domoyęj`,
`rużm`). Upsampling cannot help: glyphs are ~10 px tall where Tesseract needs 20–30.
Measured as out-of-vocabulary rate against a 62k-word vocabulary built from the five
existing books; the same measure scores known-good text at 0.1%.

**Decision: read the pages with a vision model instead.** A page photo is perfectly
legible to a human and to Claude; only Tesseract fails.

## Phase 2 — pipeline supports image-source books  ✅

- [x] `pipeline/books.py`: `pd`/`Gorska` entry plus a `mode` field — `"text"` (default)
      or `"image"`. `mode()` accessor; the pre-OCR filename pattern covers the only file.
- [x] `pipeline/extract.py`: `mode == "image"` renders every page to
      `data/images/<book_id>/pNNN.jpg` (100 dpi ≈ native, quality 80) and writes the
      usual `data/text/<Book>.json` with an `image` path and an empty `text` per page.
      Re-runs skip existing JPEGs. 541 images, 54 MB, 18 s.
- [x] `pipeline/transcribe.py` (new): `status` / `plan N` / `merge [--force]`.
      Merges agent transcriptions from `data/transcripts/<book_id>/*.json` back into
      `data/text/<Book>.json`. Idempotent and resumable — a page that already has text
      is kept unless `--force`; an unknown page number is an error, never a silent drop.
- [x] Tests: registry resolves `pd` and its mode; merge fills only empty pages,
      `--force` overwrites, unknown page raises. `pytest pipeline/tests` green (29).
- [x] Regression gate: re-running `extract.py` left `data/text/` for the five existing
      books byte-identical (`git diff --stat data/text/` empty).

Once transcription is merged, `pd` is an ordinary text book: **`chunk.py`,
`assemble.py` and `build_core.py` need no special case at all.**

## Phase 2b — transcription waves (Sonnet subagents)  ✅

Model chosen by measurement, not by price. Pilot on pages 120 / 250 / 400, scored
against a first-hand reading of the same images:

| | numbers correct (p400) | facts (p120) |
|---|---|---|
| **Sonnet 5** | **35/35** | verbatim, authors and years correct |
| Haiku 4.5 | 33/35 | mis-attributed the 1925 classification (dropped McCalla i Box), `Cattalig` for `Cattabrig`, a Cyrillic `у` inside a word, invented words |

Haiku's failures are silent and factual — exactly what produces confidently wrong
answer keys. **Use Sonnet for transcription.**

- [x] Batches of ~20 pages per subagent (agent overhead dominates a 3-page batch),
      ~8 subagents in parallel, ~27 batches for 541 pages.
- [x] Each subagent writes `data/transcripts/pd/pAAA-BBB.json`
      (`{"pages":[{"page":N,"text":"..."}]}`), verbatim Polish, `[?]` for illegible,
      hyphenated line breaks joined, running heads dropped.
- [x] `python pipeline/transcribe.py merge` after each wave. Result: **541/541 pages,
      130 686 words** — ~242 words per page.
- [x] Spot-check: page 330 transcribed verbatim against the photo, table and footnote
      included. (An out-of-vocabulary sweep scores this text at 13%, but the flagged
      tokens are real perio terms and bibliography surnames — unlike the OCR attempt,
      whose flagged tokens were noise.)
- [x] `python pipeline/chunk.py` → **159 `pd` chunks**. Gate passed: zero existing
      chunks changed or lost, zero `generated` flags lost.

## Phase 3 — generation waves (parallel subagents)

Protocol: `pipeline/GENERATION.md`, unchanged — agents read chunk **text**, because
transcription already turned this book into a text book. Batches of ~25 chunks per
subagent, several in parallel; the orchestrator marks state and assembles once per wave.

- [x] One wave, 8 subagents × ~20 chunks, covering all 159 chunks.
      Perio-specific traps to check: mangled numbers in classifications
      (stopnie zaawansowania, wskaźniki API/BOP/CPITN, mm of attachment loss) — a wrong digit
      is an invisible wrong answer. Verify every numeric claim against the chunk.
- [x] **405 questions** written; 20 chunks skipped as junk (front matter, contents,
      `Piśmiennictwo`, index) — each skip verified to be non-prose.
- [x] Skipped junk per GENERATION.md: TOC dot-leaders, `Piśmiennictwo`, figure/table captions,
      index, and history/institutional prose (person / city / year answers).
- [x] Mixed in `combined` (16) and `clinical` (5) types — perio is well suited: vignettes on
      diagnosis and treatment staging, plus multi-statement questions on classification.
- [x] After the wave (orchestrator only):
      `python pipeline/mark_generated.py pd-cNNN pd-cNNN`
      `python pipeline/build_core.py`
      `python pipeline/assemble.py`
      Commit `data/questions.json` + `docs/questions.json` + `data/core.json` + `data/state.json`.

Core subset needs no new curation: `Gorska` is not in `core_curated.json`, so `build_core.py`
covers it by rule (every `combined`/`clinical` + one per otherwise-unrepresented chunk).

## Phase 4 — web app

The app is `docs/` (GitHub Pages), **not** `web/` as AGENTS.md still claims.

- [x] `docs/app.js`: appended `["Gorska", "Górska — periodontologia"]` to `BOOKS`.
      Checkbox list and counts are derived automatically; a saved localStorage selection
      simply won't include the new book until the user ticks it (existing fallback handles
      the empty-selection case).
- [x] Decided: no UI grouping — the app filters by book and ignores `domain`. Current app filters by book only
      and ignores `domain` — leave the UI as-is unless the user asks for domain grouping.
- [x] Served and smoke-tested: `python -m http.server -d docs 8000` — book appears with a
      plausible count, filter works, source line shows `Gorska, s. X–Y`.

## Phase 5 — docs & close-out

- [x] `AGENTS.md`: added `pd`/`Gorska` to the book table, add the new OCR command,
      and fix the stale `web/` references → `docs/`.
- [x] `pytest pipeline/tests` green (29 passed).
- [x] Final counts: **3231 questions** (was 2826), **1390 core** (was 1245).
      Per book: Tom2 863 · Janczuk 571 · Tom1 543 · Tom3 457 · **Gorska 405** · Arabska 392.
      Answer keys spread A 90 / C 85 / B 81 / E 76 / D 73; zero malformed questions,
      zero bad page references, zero duplicate ids.

## Risks

| Risk | Mitigation |
|---|---|
| OCR unusable (materialised) | Replaced by vision transcription; see Phase 1 |
| A transcription silently paraphrases instead of copying | Sonnet chosen on a scored pilot; spot-check pages against images before generating |
| Re-chunk drifts existing page ranges | Phase 2 `git diff data/state.json` gate |
| Wrong numbers in perio indices/classifications | Verify each numeric claim against chunk text; flag suspicious OCR digits |
| Hand-edited core flags lost | Never edit `questions.json`; only `core.json` via `build_core.py` |
