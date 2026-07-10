# AGENTS.md — med-exam

Guidance for AI agents (and humans) working in this repo.

## What this project is

An interactive MCQ test bank (~1000 questions) built from Polish maxillofacial-surgery
textbooks, to prepare foreign doctors for the Polish medical verification exam
(nostryfikacja / LDEW). Two parts: a build pipeline that turns PDFs into
`data/questions.json`, and a static web app that serves the quiz.

## Language rule (important)

- **All exam content is Polish** — questions, options, explanations, topics, and the
  web app's UI text. Do not translate content to English.
- **All project artifacts are English** — code, comments, docs, this file, commit
  messages, variable names, JSON keys.

## Layout

- `books/` — source PDFs. **Gitignored** (up to ~200 MB each). Never commit.
- `pipeline/` — Python: `extract.py`, `chunk.py`, `assemble.py`, `schema.py`.
- `data/` — `chunks/` and `questions/` are intermediate (gitignored); `state.json`
  tracks progress; `questions.json` is the committed final product.
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
python pipeline/extract.py     # PDFs -> cleaned chapter text
python pipeline/chunk.py       # chapters -> data/chunks/*.json
# (agent generates data/questions/<chapter>.json here)
python pipeline/assemble.py    # merge + validate -> data/questions.json, copy to web/
```
Serve the app locally: `python -m http.server -d web 8000` then open localhost:8000.

## Conventions

- Python 3.11, standard style; keep pipeline scripts small and single-purpose.
- Vanilla JS web app — **no build step, no framework** (GitHub Pages serves it raw).
- IDs: `t{2|3}-ch{NN}-{NNN}` (book, chapter, running number).
- Don't add: backend, exam/timed mode, LLM review pass — out of scope for v1.

## Do not

- Commit `books/` or intermediate `data/chunks`, `data/questions`.
- Invent page references — `source.pages` must come from the chunk being used.
- Mix languages: no English content, no Polish code identifiers.
