# med-exam — Design Spec

**Date:** 2026-07-10
**Goal:** Build an interactive test bank (~1000 MCQ) from Polish maxillofacial-surgery textbooks to prepare foreign doctors for the Polish verification exam (nostryfikacja / LDEW). Content in Polish; project code/docs in English.

## Source material

- `books/Tom2. Mansur Rahnama.pdf` — 584 pages
- `books/Tom3. Mansur Rahnama.pdf` — 360 pages
- Topic: chirurgia szczękowo-twarzowa (oral & maxillofacial surgery).
- **PDFs have an embedded text layer** — Polish text extracts cleanly via pymupdf. No OCR needed. Minor artifacts: line-break hyphenation (`szczę-\nkowy`), figure-heavy pages with thin text.
- Books are atlases/textbooks, not question banks → questions are **generated** from content, not extracted. (Hybrid target collapses to pure generation.)

## Exam format target

LDEW / nostryfikacja: single-best-answer MCQ, 5 options (A–E), exactly one correct.

## Architecture

Two halves:

1. **Build pipeline** — turns PDFs into `data/questions.json`. Deterministic parts in Python (free); generation done **in-session by the Claude Code agent** (subscription — no Anthropic API key available).
2. **Web app** — static HTML/JS site reading `questions.json`, hosted on GitHub Pages. Fully free/static once the bank exists.

### Repo layout
```
med-exam/
  books/                    # source PDFs (gitignored — too large, up to 200MB)
  pipeline/
    extract.py              # PDF → cleaned text per chapter (dehyphenate, page tags)
    chunk.py                # chapter text → topical chunks with chapter/page refs
    assemble.py             # merge per-chunk question files → questions.json + validate
    schema.py               # question schema + validator (shared)
  data/
    chunks/                 # intermediate: one JSON per chunk (gitignored)
    questions/              # intermediate: generated questions per chapter (gitignored)
    state.json             # progress: which chapters/chunks done (resumable)
    questions.json          # FINAL bank = the product (committed)
  web/
    index.html app.js style.css
    questions.json          # copy of data/questions.json served to the app
  AGENTS.md
  docs/superpowers/specs/
```

## Pipeline flow

1. **extract.py** — for each PDF: pymupdf `get_text` per page; dehyphenate (join `-\n`); tag each block with `{book, page}`; group into chapters via heading regex (`^\d+(\.\d+)*\.\s+Title`). Output cleaned chapter text with page ranges.
2. **chunk.py** — split each chapter into ~1000-token semantic chunks; each chunk keeps `{book, chapter, topic, pages[], text}`. Write to `data/chunks/*.json`.
3. **Generation (agent, in-session)** — process **one chapter per run**, ~50 questions/run (count flexes with chapter size: big → ~50, small → ~25–30, always grounded in real content, no padding). Agent reads the chapter's chunk files and writes MCQ to `data/questions/<chapter>.json`. Parallelizable across chunks with subagents. Progress recorded in `data/state.json` → stop/resume anytime, across sessions.
   - **No separate review pass.** Correctness comes from grounding each question in the chunk text at generation time, plus a mandatory source reference for human spot-check.
4. **assemble.py** — merge all `data/questions/*.json`, validate against schema, dedupe by id, write `data/questions.json`; copy to `web/questions.json`.

### Question schema
```json
{
  "id": "t2-ch09-001",
  "topic": "Chirurgia zatok szczękowych",
  "source": { "book": "Tom2", "pages": [10, 12] },
  "question": "…",
  "options": { "A": "…", "B": "…", "C": "…", "D": "…", "E": "…" },
  "correct": "C",
  "explanation": "…"
}
```
Validation rules: `id` unique; exactly 5 options A–E, all non-empty; `correct` ∈ {A–E}; `question`, `explanation`, `topic` non-empty; `source.pages` non-empty. All natural-language fields in **Polish**.

### Generation prompt contract (agent)
- Input: chunk text (Polish) + chapter/topic/pages.
- Output: MCQ objects matching schema. Single best answer, 5 plausible options, one unambiguously correct per the chunk text. Explanation (Polish) states why correct and cites the concept. `source.pages` = chunk page range. No question answerable only from outside the chunk.

## Web app

Single static page, vanilla JS, no build step.

- **Start screen:** choose mode — **All in order** / **Random** / **By topic** (topic dropdown). Start button.
- **Quiz screen:** one question, 5 options (A–E). Click an option → lock it; show correct in green, chosen-wrong in red, reveal explanation + source ref (`Źródło: Tom2, s. 10–12`). Next button.
- **Progress:** score counter + progress bar. `localStorage` persists answered set + running score → resume on return; a reset button clears it.
- UI text in **Polish** (exam-taker facing). Clean, minimal flow — no over-engineering.
- `questions.json` (~1k Q, ~1–2 MB) loaded client-side once.

## Hosting

GitHub Pages, serving `web/`. Static, free, public URL. Deploy = push to repo.

## Testing

- **Pipeline:** unit test dehyphenation; schema validator test (rejects malformed: missing option, bad `correct`, empty field); `assemble.py` fails loudly on any invalid question.
- **Web:** smoke test that `questions.json` loads and a question renders; manual click-through of the three modes.

## Out of scope (v1)

Exam mode (timed 200-Q mock), any backend, user accounts, separate LLM review pass, Anthropic-API-driven batch generation.

## Key decisions log

- Nostryfikacja/LDEW target → 5-option single-best MCQ.
- Text PDFs → extract, no OCR.
- No API key → generation performed in-session by the agent, batched one chapter at a time (~50 Q/run), resumable via `state.json`.
- No self-review pass; trust grounded generation + mandatory source ref.
- Hosting: GitHub Pages, static vanilla-JS app.
