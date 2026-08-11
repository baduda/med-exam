# Wave 5 — three new books (Tom1, Jańczuk, Arabska)

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Extend the bank from 1320 to ~2700 questions by adding three books, and let the
user pick any combination of books in the web app.

**Targets:** Tom1 500 · Jańczuk 600 · Arabska 300 (minimum, hard floor).

## Source inventory (measured 2026-08-11)

| File | book_id | Pages | Words of embedded text | Note |
|---|---|---|---|---|
| `Tom1. Mansur Rahnama.pdf` | `t1` | 592 | 277 849 | same series as Tom2/Tom3 |
| `Sormatologia zachowawcza z endodoncją- Jańczuk 2014.pdf` | `jz` | 538 | 182 230 | conservative dentistry + endo |
| `Arabska_Przedpełska_B,_Pawlicka_H_Współczesna_endodoncja_w_praktyce.pdf` | `ae` | 414 | **0** | image-only scan → needs OCR |

Existing bank: 1320 Q (Tom2 863, Tom3 457), 367 chunks, 600 flagged `core: true`.

## Global constraints (unchanged from v1)

- Content Polish; code/docs/JSON keys English.
- 5 options A–E, exactly one correct; `assemble.py` randomises the correct position.
- `source.pages` must come from the chunk. Never invented.
- Generation is agent-in-session (no API key), resumable via `data/state.json`.
- `books/`, `data/chunks/`, `data/questions/` stay gitignored.

---

## Phase 1 — OCR the Arabska scan

Blocker for the third book. Verify quality on a sample **before** running the full 414 pages.

- [ ] Install tooling: `brew install ocrmypdf tesseract-lang` (needs the `pol` traineddata).
- [ ] Confirm `tesseract --list-langs` includes `pol`.
- [ ] OCR a 5-page sample:
      `ocrmypdf -l pol --pages 40-44 --force-ocr books/Arabska*.pdf /tmp/ae-sample.pdf`
- [ ] Extract the sample text and read it. **Quality gate:** Polish diacritics (ą/ć/ę/ł/ń/ó/ś/ź/ż)
      preserved, medical terms legible (`miazga`, `opracowanie kanału`, `ćwiek gutaperkowy`),
      < ~2% garbled tokens. If it fails, try `--oversample 400` / deskew; if it still fails,
      STOP and report — do not generate questions from garbled OCR.
- [ ] Run full OCR → `books/Arabska_ocr.pdf` (keep the original untouched).
- [ ] Add the OCR command to `AGENTS.md` so the step is reproducible.

## Phase 2 — pipeline supports non-`TomN` books

`chunk.book_prefix()` derives the id from digits in the filename: `"Sormatologia … 2014"`
would become `t2014` and Arabska would become `t` (empty). Must be replaced with an explicit map.

- [ ] Add a `BOOKS` registry (one place, imported by both `extract.py` and `chunk.py`):
      filename-glob → `{book_id, book_label, domain}`.
      - `Tom1*` → `t1`, "Tom1", domain `chirurgia`
      - `Tom2*` → `t2`, `Tom3*` → `t3`, domain `chirurgia` (keep existing ids stable)
      - `Sormatologia*Jańczuk*` → `jz`, "Jańczuk 2014", domain `zachowawcza`
      - `Arabska*` → `ae`, "Arabska–Pawlicka", domain `zachowawcza`
- [ ] `extract.py`: use the registry instead of `pdf_path.stem.split(".")[0]`; unknown file → error out loudly, never guess.
- [ ] `chunk.py`: use `book_id` from the registry; delete `book_prefix()`.
- [ ] Unit test: registry resolves all five filenames; unknown filename raises.
- [ ] Re-run `extract.py` + `chunk.py`. **Verify existing `t2-*`/`t3-*` chunk ids and page
      ranges are byte-identical** (diff `data/state.json` against git HEAD for those keys) —
      the 1320 existing questions reference them.
- [ ] Expected new chunks: ~400 (`t1`), ~260 (`jz`), ~?? (`ae`, after OCR).

## Phase 3 — question generation waves (parallel subagents)

Per `pipeline/GENERATION.md`. Run `assemble.py` after each wave, commit
`data/questions.json` + `docs/questions.json`.

Chunk selection: skip junk (TOC dot-leaders, `Piśmiennictwo`, figure captions, index).
There are more chunks than needed — pick for exam relevance, do not grind every chunk.

### Parallelisation

Each subagent owns a disjoint chunk range and writes only `data/questions/<chunk_id>.json`,
so there is no write contention. Rules that keep it safe:

- **One subagent = one contiguous chunk range**, ~15–20 chunks → ~40–50 Q per agent.
  4–6 agents per wave.
- **Subagents never touch `data/state.json`** — the orchestrator marks `generated: true`
  after collecting results. Concurrent writes to a single JSON file would lose entries.
- **Subagents never run `assemble.py` or `git`** — orchestrator only, once per wave.
- Each subagent prompt must inline: the chunk-id range, the book_id, the full
  `pipeline/GENERATION.md` rules (styles, Polish-only, option-length rule, real
  `source.pages`), and its style quota (e.g. "12 single, 4 combined, 4 clinical").
- Subagent returns a summary (chunks done, chunks skipped as junk, Q count), not the
  question text — the files on disk are the artifact.
- After each wave the orchestrator runs `assemble.py`; validation errors are attributed
  back to the owning chunk file and fixed before commit.

### Waves

- [ ] **Tom1 → 500 Q.** ~200 chunks × 2–3 Q. Mix: ~60% single, ~20% combined, ~20% clinical.
      ~10 subagents across 2–3 waves.
- [ ] **Jańczuk → 600 Q.** ~230 chunks. Highest LDEK yield (próchnica, materiały,
      endodoncja, profilaktyka). Same style mix.
- [ ] **Arabska → 300 Q.** Endo only. **Deduplicate against Jańczuk:** prefer technique,
      instrumentation, retreatment, working-length/irrigation protocol content that Jańczuk
      covers thinly. Dedup does NOT parallelise well — run Arabska **after** Jańczuk is
      assembled, and give each subagent the list of `jz-*` question stems for its topic so
      it can avoid restatements. A final single-agent dedup pass over all `ae-*` questions
      catches what the parallel agents missed.
- [ ] After each wave: `python pipeline/assemble.py` must exit 0.

- [ ] **Tom1 → 500 Q.** ~200 chunks × 2–3 Q. Mix: ~60% single, ~20% combined, ~20% clinical.
- [ ] **Jańczuk → 600 Q.** ~230 chunks. Highest LDEK yield (próchnica, materiały,
      endodoncja, profilaktyka). Same style mix.
- [ ] **Arabska → 300 Q.** Endo only. **Deduplicate against Jańczuk:** prefer technique,
      instrumentation, retreatment, working-length/irrigation protocol content that Jańczuk
      covers thinly. Before writing a question, check it is not a near-restatement of an
      existing `jz-*` one.
- [ ] After each wave: `python pipeline/assemble.py` must exit 0.

## Phase 4 — book selection in the web app

User requirement: pick **any single book or any combination**.

- [ ] Add `book` domain metadata to the app: derive from `q.source.book`, label via a
      JS-side map matching the Phase-2 registry.
- [ ] Replace the single "Zakres" select with:
      - `Zakres`: Kluczowe (LDEK) / Wszystkie — keep as is.
      - `Książki`: multi-select checkbox group (Tom1, Tom2, Tom3, Jańczuk, Arabska),
        all checked by default; at least one must stay checked.
- [ ] `buildQueue()` filters by scope **and** the selected book set.
- [ ] Persist the selection in `localStorage` alongside progress.
- [ ] Update the counter line: `N pytań (z M)` reflecting both filters.
- [ ] Update `index.html` lead text + `<title>` — the bank is no longer only
      chirurgia szczękowo-twarzowa.
- [ ] Mobile: the checkbox group must keep ≥44px touch targets (see existing phone media query).

## Phase 5 — rebuild the LDEK core subset

Currently 600 of 1320. After the waves the bank is ~2700, so the core flag must be recomputed
across the whole bank, not just appended to.

- [ ] Re-flag `core: true` targeting ~1200 questions: all `combined` + `clinical`,
      plus CEM-relevance ranking, plus ≥1 per chunk so coverage stays complete.
- [ ] Verify per-book core counts are roughly proportional to book size — no book
      should be absent from the core scope.

## Phase 6 — docs

- [ ] `AGENTS.md`: five books not two; the `BOOKS` registry; the OCR step; new id prefixes.
- [ ] `pipeline/GENERATION.md`: id format is now `<book_id>-c<NNN>-<NNN>` with non-`t{N}`
      prefixes; add the Arabska/Jańczuk dedup rule.

## Verification (before calling it done)

- [ ] `python pipeline/assemble.py` exits 0 and reports ~2700 questions.
- [ ] `python -m unittest discover pipeline/tests` passes.
- [ ] Per-book counts: t1 ≥500, jz ≥600, ae ≥300, t2/t3 unchanged at 863/457.
- [ ] No duplicate ids; every `source.pages` within its book's page count.
- [ ] Serve `docs/` locally; check each book filter combination yields the expected count,
      and that "Kluczowe" + one book still produces a non-empty queue.

## Risks

- **OCR quality** is the main unknown. Gate in Phase 1 is a hard stop, not advisory.
- **Chunk-id drift** in Phase 2 would orphan 1320 existing questions. Diff before committing.
- **Arabska/Jańczuk overlap** — if dedup proves too costly, report and let the user decide
  whether to cut Arabska below 300 rather than shipping restated duplicates.
- **Parallel-agent quality drift** — separate agents produce inconsistent difficulty and
  can duplicate each other near range boundaries. Mitigation: identical inlined rules in
  every prompt, disjoint ranges, and a spot-check of ~20 random questions per wave before
  committing.
