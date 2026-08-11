# AGENTS.md — med-exam

Guidance for AI agents (and humans) working in this repo.

## What this project is

An interactive MCQ test bank built from Polish dental textbooks, to prepare foreign
doctors for the Polish medical verification exam (nostryfikacja / LDEW). Two parts:
a build pipeline that turns PDFs into `data/questions.json`, and a static web app
that serves the quiz.

Five source books across two domains, declared in `pipeline/books.py`:

| book_id | `source.book` | Title | Domain |
|---|---|---|---|
| `t1`/`t2`/`t3` | `Tom1`/`Tom2`/`Tom3` | Rahnama, *Chirurgia stomatologiczna i szczękowo-twarzowa* | chirurgia |
| `jz` | `Janczuk` | Jańczuk, *Stomatologia zachowawcza z endodoncją* (2014) | zachowawcza |
| `ae` | `Arabska` | Arabska-Przedpełska, Pawlicka, *Współczesna endodoncja w praktyce* | zachowawcza |

The web app lets the user practise any combination of books.

## Language rule (important)

- **All exam content is Polish** — questions, options, explanations, topics, and the
  web app's UI text. Do not translate content to English.
- **All project artifacts are English** — code, comments, docs, this file, commit
  messages, variable names, JSON keys.

## Layout

- `books/` — source PDFs. **Gitignored** (up to ~800 MB each). Never commit.
- `pipeline/` — Python: `books.py` (source registry), `extract.py`, `chunk.py`,
  `assemble.py`, `mark_generated.py`, `schema.py`.
- `data/` — `chunks/` and `questions/` are intermediate (gitignored); `state.json`
  tracks progress; `core_curated.json` holds the frozen hand-ranked LDEK picks and
  `core.json` the generated subset; `questions.json` is the committed final product.
- `web/` — static site (GitHub Pages). Ships its own copy of `questions.json`.
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
python pipeline/extract.py                       # PDFs -> per-page text
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

### OCR

One book is an image-only scan and must be OCR'd before extraction. The output is
what `books.py` registers; the original stays as an ignored source:

```bash
ocrmypdf -l pol --force-ocr --jobs 8 \
  "books/Arabska_Przedpełska_B,_Pawlicka_H_Współczesna_endodoncja_w_praktyce.pdf" \
  books/Arabska_ocr.pdf
```
Serve the app locally: `python -m http.server -d web 8000` then open localhost:8000.

## Conventions

- Python 3.11, standard style; keep pipeline scripts small and single-purpose.
- Vanilla JS web app — **no build step, no framework** (GitHub Pages serves it raw).
- IDs: `<book_id>-c{NNN}-{NNN}` (book, chunk, running number) — e.g. `jz-c100-002`.
  Book ids come from `pipeline/books.py`; never derive them from the filename.
- Don't add: backend, exam/timed mode, LLM review pass — out of scope for v1.

## Do not

- Commit `books/` or intermediate `data/chunks`, `data/questions`.
- Invent page references — `source.pages` must come from the chunk being used.
- Mix languages: no English content, no Polish code identifiers.
- Hand-edit `core` flags into `data/questions.json` — it is a build artifact, and the
  next `assemble.py` run overwrites it. The subset lives in `data/core.json`.
- Let generation agents write `data/state.json`, run `assemble.py`, or run `git`.
  Concurrent writers lose entries; the orchestrator does those steps once per wave.
