# AGENTS.md — med-exam

Guidance for AI agents (and humans) working in this repo.

## What this project is

An interactive MCQ test bank built from Polish dental textbooks, to prepare foreign
doctors for the Polish medical verification exam (nostryfikacja / LDEW). Two parts:
a build pipeline that turns PDFs into `data/questions.json`, and a static web app
that serves the quiz.

Thirteen source books across seven domains, declared in `pipeline/books.py`:

| book_id | `source.book` | Title | Domain |
|---|---|---|---|
| `t1`/`t2`/`t3` | `Tom1`/`Tom2`/`Tom3` | Rahnama, *Chirurgia stomatologiczna i szczękowo-twarzowa* | chirurgia |
| `jz` | `Janczuk` | Jańczuk, *Stomatologia zachowawcza z endodoncją* (2014) | zachowawcza |
| `ae` | `Arabska` | Arabska-Przedpełska, Pawlicka, *Współczesna endodoncja w praktyce* | zachowawcza |
| `pd` | `Gorska` | Górska, Konopka, *Periodontologia współczesna* (2013) | periodontologia |
| `pl` | `GorskaLDEK` | Górska (red.), *Periodontologia. Podręcznik dla studentów i do LDEK* (2022) | periodontologia |
| `mj` | `Majewski` | Majewski, *Współczesna protetyka stomatologiczna* | protetyka |
| `dj` | `Dejak` | Dejak, *Vademecum wykonywania protez stałych i ruchomych* | protetyka |
| `ok` | `Olczak` | Olczak-Kowalczyk (red.), *Współczesna stomatologia wieku rozwojowego* (2017) | pedodoncja |
| `bs` | `GorskaBlony` | Górska (red.), *Choroby błony śluzowej jamy ustnej* | błona śluzowa |
| `or` | `Ortodoncja` | Karłowska (red.), *Zarys współczesnej ortodoncji* | ortodoncja |
| `pk` | `PedoKompendium` | Olczak-Kowalczyk (red.), *Kompendium stomatologii wieku rozwojowego* | pedodoncja |

The web app lets the user practise any combination of books.

## Language rule (important)

- **All exam content is Polish** — questions, options, explanations, topics, and the
  web app's UI text. Do not translate content to English.
- **All project artifacts are English** — code, comments, docs, this file, commit
  messages, variable names, JSON keys.

## Layout

- `books/` — source PDFs. **Gitignored** (up to ~800 MB each). Never commit.
- `pipeline/` — Python: `books.py` (source registry), `extract.py`, `scan.py`,
  `transcribe.py`, `chunk.py`, `assemble.py`, `mark_generated.py`, `build_core.py`,
  `schema.py`.
- `data/` — `chunks/`, `questions/`, `images/` and `transcripts/` are intermediate
  (gitignored); `pagemap/` holds the verified pdf→printed page maps for `scan` books;
  `state.json`
  tracks progress; `core_curated.json` holds the frozen hand-ranked LDEK picks and
  `core.json` the generated subset; `questions.json` is the committed final product.
- `docs/` — static site (GitHub Pages serves this directory). Ships its own copy of
  `questions.json`.
- `docs/superpowers/specs/` — design spec. Read it before changing architecture.

## How generation works (no API key)

There is **no Anthropic API key** — the user is on a Claude subscription. So MCQ
generation is done **by the agent in-session**, not by a script calling the API.

- Python does only deterministic, free work: extract, chunk, validate, assemble.
- The agent reads chunk files from `data/chunks/` and **writes questions** to
  `data/questions/<chapter>.json`, following the schema in `pipeline/schema.py`.
- Work **one chapter per run**, ~50 questions (flex with chapter size — never pad
  with filler or duplicates; every question must be grounded in the chunk text).
- Record what's done in `data/state.json` so runs are **resumable** across sessions.
- Each question **must** carry a real `source.pages` reference from its chunk.

## Question schema

```json
{
  "id": "t2-ch09-001",
  "topic": "…", "source": { "book": "Tom2", "pages": [10, 12] },
  "question": "…",
  "options": { "A": "…", "B": "…", "C": "…", "D": "…", "E": "…" },
  "correct": "C", "explanation": "…"
}
```
Rules: unique `id`; exactly 5 non-empty options A–E; `correct` ∈ {A–E}; all NL fields
Polish and non-empty. `assemble.py` rejects anything malformed — run it after generating.

## Commands

```bash
python pipeline/extract.py                       # PDFs -> per-page text (or page images)
python pipeline/transcribe.py status             # image books: transcription coverage
python pipeline/transcribe.py merge              # agent transcripts -> per-page text
python pipeline/chunk.py                         # text -> data/chunks/*.json
# (agents generate data/questions/<chunk>.json here — see pipeline/GENERATION.md)
python pipeline/mark_generated.py t1-c001 t1-c108  # record a finished wave
python pipeline/build_core.py                    # refresh the LDEK subset -> data/core.json
python pipeline/assemble.py                      # merge + validate -> data/questions.json + docs/
```

### The "Kluczowe (LDEK)" subset

`data/core.json` is a generated list of question ids; `assemble.py` stamps
`core: true` on them. The subset used to live solely inside the built
`data/questions.json`, so a single `assemble.py` run erased 600 curated flags —
do not reintroduce that shape.

Two inputs:

- `data/core_curated.json` — the original Tom2/Tom3 picks, hand-ranked for CEM
  relevance. **Frozen input, read-only for tooling**; that judgement cannot be
  re-derived from the text.
- everything else is rule-based: every `combined` and `clinical` question, plus
  one question from each otherwise-unrepresented chunk.

`pipeline/build_core.py` regenerates `core.json` from both and is **idempotent**.
It reads the per-chunk sources under `data/questions/`, not the built bank, so it
can run before or after `assemble.py`. It exits non-zero if a book ends up with
no core questions at all. Re-run after every generation wave.

### Books typeset as spreads

The Dejak vademecum has a text layer, but one PDF page holds two facing printed
pages. Unlike the Górska LDEK scan the numbering is a formula — `left = 2 * pdf - 2`
— so no hand-read pagemap is needed. Such a book is declared `"mode": "spread"` and
`extract.py` emits each spread whole, numbered with its left printed page. It is not
split geometrically: the gutter is off-centre and the page is rotated 90 degrees, so
a midpoint clip cuts words in half (`powierzchnia` -> `owierzchnia`).

### Books without a text layer

Four books ship no text. They are handled differently, and the difference is
measured, not stylistic — OCR a sample and count garbled tokens against the <2%
gate before choosing.

**OCR (Arabska).** A clean 1163×1613 flatbed scan: OCR yields 0.1% garbled tokens.
The OCR output is what `books.py` registers; the original stays an ignored source:

```bash
ocrmypdf -l pol --force-ocr --jobs 8 \
  "books/Arabska_Przedpełska_B,_Pawlicka_H_Współczesna_endodoncja_w_praktyce.pdf" \
  books/Arabska_ocr.pdf
```

**OCR (Górska, błona śluzowa).** A 300 dpi flatbed scan of a colour atlas, one
printed page per PDF page, no text layer: `ocrmypdf` yields 0.6% garbled tokens.
Its printed numbering starts 13 pages into the PDF, which no other book needed, so
the registry entry carries `page_offset: -13` and `extract.py` drops the pages that
fall below 1. The offset was checked against the footer of every page that prints
one — 131 of 131 agree.

```bash
ocrmypdf -l pol --force-ocr --jobs 8 \
  "books/Błony śluzowe - Górska.pdf" books/Gorska_blony_ocr.pdf
```

**Spread OCR (Górska LDEK 2022).** A flat, sharp scan with no text layer, one image
per *spread* — a single PDF page holds two facing book pages. Tesseract reads it at
~0.4% garbled tokens once each spread is cut in half and rendered at 400 dpi. Such a
book is declared `"mode": "scan"`, and `scan.py` does the split + OCR from
`extract.py`; after that it is an ordinary text book.

**Spread OCR, bound off-centre (Zarys współczesnej ortodoncji).** Another
text-less spread scan, 0.7% garbled tokens. Two things differ from the Górska
LDEK scan, and both are declared in the registry:

- Its binding shadow sits at ~0.52 of the page width and one page's text starts
  at 0.486, so a midpoint clip eats into the right-hand page. `gutter_split: true`
  makes `scan.py` cut at the darkest column band instead (the shadow is by far the
  strongest peak in the ink profile).
- Its numbering is *nearly* a formula — `left = 2 * spread`, but two spreads (55
  and 60) are second captures of the ones before them, and each duplicate shifts
  everything after it by two pages. The map in `data/pagemap/or.json` records that,
  and the tail (spreads 197-205, a photo insert plus the skorowidz) is left out.
  The two breaks were found by OCR-ing the outer bottom corner of every half: 154
  spreads carry a readable printed number and none contradicts the map.

Two traps this scan taught us, both recorded in `scan.py`:

- **Do not binarize the body.** Binarizing to recover the white-on-red page numbers
  costs real text — `250 200 mg` for `250–500 mg`. Render plain grayscale.
- **Printed page numbers cannot be computed.** The scan mixes true spreads
  (verso|recto) with misaligned captures (recto|verso), duplicates some spreads and
  drops others, so no formula maps spread → page. The map in
  `data/pagemap/<book_id>.json` was read off the header bands by eye and is frozen
  input. For `pl` it covers 220 of 232 pages. The absent ones are blank versos facing
  chapter openers (8, 26, 66, 92, 124, 190, 198, 210, plus 1) and the tail of chapter
  3's bibliography (36–38) — no prose is lost.
- **Known defect:** chapter openers print their number at the foot of the page, not in
  the header band, and the map's "right = left + 1" rule therefore labels four of them
  one too low (spreads 17, 35, 63, 100 → pages 27, 67, 125, 199). Nine questions cite
  the low number. See the wave-7 plan for the fix.

**Page OCR with a drifting offset (PEDO kompendium).** A 320 dpi scan with no text
layer, photographed one printed page per PDF page rather than as spreads. Tesseract
reads it at 0.4% garbled tokens. It is declared `"mode": "scan"` with no
`gutter_split`, and `scan.py` skips the split when the pagemap is keyed `"pages"`
instead of `"spreads"`.

Its numbering is neither a formula nor a constant offset: the scan drops 28 pages
scattered through the book, so pdf→printed drifts from +6 at the front to +28 at the
back. The map was recovered rather than read by eye — the outer bottom corners of all
420 pages were OCR'd digits-only, then fitted by DP over *non-decreasing* offsets
(pages are only ever dropped, never added), scoring the parity rule that verso numbers
sit in the left corner and recto in the right. The fit agrees with 238 of the 268
pages that yielded a corner number; the 30 disagreements are figure-caption numbers
(`1`, `4`, `7`) with no page number in the corner at all. Spot checks by full-page OCR
at every offset jump confirm it. Front matter (pdf 1-4) is left out of
`data/pagemap/pk.json`, which covers printed pages 11-448.

**Vision transcription (Górska 2013).** Phone photos at 689×1024 (~96 dpi) with curved
lines and a finger in frame. OCR — including `--deskew --oversample 400` — returns
~20% garbled tokens, ten times the <2% gate, and upsampling cannot recover glyphs
that are 10 px tall. Such a book is declared `"mode": "image"` in `books.py`:

- `extract.py` renders its pages to `data/images/<book_id>/pNNN.jpg` and writes the
  usual `data/text/<Book>.json` with an empty `text` per page.
- Subagents read those images and write verbatim transcriptions to
  `data/transcripts/<book_id>/*.json` (`{"pages":[{"page":N,"text":"…"}]}`).
- `transcribe.py merge` folds them into `data/text/<Book>.json`, idempotently.
- After that the book is an ordinary text book — `chunk.py`, `assemble.py` and
  `build_core.py` have no special case for it.

Transcribe with **Sonnet, not Haiku**: on a scored three-page pilot Haiku
mis-attributed a classification, dropped digits from measurements and invented
Polish words — silent errors that become confidently wrong answer keys.

Serve the app locally: `python -m http.server -d docs 8000` then open localhost:8000.

## Conventions

- Python 3.11, standard style; keep pipeline scripts small and single-purpose.
- Vanilla JS web app in `docs/` — **no build step, no framework** (GitHub Pages
  serves it raw). Adding a book means one row in `BOOKS` in `docs/app.js`.
- IDs: `<book_id>-c{NNN}-{NNN}` (book, chunk, running number) — e.g. `jz-c100-002`.
  Book ids come from `pipeline/books.py`; never derive them from the filename.
- Don't add: backend, exam/timed mode, LLM review pass — out of scope for v1.

## Do not

- Commit `books/` or intermediate `data/chunks`, `data/questions`, `data/images`,
  `data/transcripts`.
- Invent page references — `source.pages` must come from the chunk being used.
- Mix languages: no English content, no Polish code identifiers.
- Hand-edit `core` flags into `data/questions.json` — it is a build artifact, and the
  next `assemble.py` run overwrites it. The subset lives in `data/core.json`.
- Let generation agents write `data/state.json`, run `assemble.py`, or run `git`.
  Concurrent writers lose entries; the orchestrator does those steps once per wave.
