# Generation protocol (agent-run)

Questions are generated **by the Claude Code agent in-session** (no Anthropic
API key). Work is resumable via `data/state.json` (`generated` flag per chunk).

## Per chunk
1. Read `data/chunks/<chunk_id>.json` → `{chunk_id, book, pages, text}`.
2. **Skip junk chunks** — if the text is mostly table-of-contents (dot-leader
   runs `.....`), a bibliography/`Piśmiennictwo` list of "Author A., Author B.:"
   citations, or OCR garble with few full Polish sentences, skip it (mark
   `generated: true`, write no questions). Only generate from real prose.
3. Write **2–3** single-best-answer MCQ grounded ONLY in that chunk's text:
   - Format: 5 options A–E, **exactly one correct**, 4 plausible Polish
     distractors (standard single-best-answer — matches LEW/LDEW; no
     multi-select, no combined "1 i 2" answers).
   - Everything in **Polish**: `question`, `options`, `explanation`.
   - `source` = `{"book": <book>, "pages": <chunk pages>}`. Never invent pages.
   - `id` = `<chunk_id>-NNN` (e.g. `t2-c016-001`), running per chunk.
   - `explanation`: one–two Polish sentences on why the answer is correct,
     tied to the chunk content.
   - No `topic` field needed (UI has no topic filter).
   - **Keep the 5 options similar in length and detail** — do NOT make the
     correct one conspicuously longer/more qualified (a common tell). The
     correct-answer *position* is auto-randomised by assemble.py, so don't
     worry about which letter you assign; just avoid the length giveaway.
4. Write the list to `data/questions/<chunk_id>.json`.

## Batch / resume
- Process a range of chunks per run; set `generated: true` for each done chunk.
- After a batch: `python pipeline/assemble.py` (validates + rebuilds
  `data/questions.json` and `web/questions.json`). Fix any reported errors.
- Commit `data/questions.json` + `web/questions.json` (the per-chunk files
  under `data/questions/` are gitignored).
- v1 target ~300 questions; expand later by generating from remaining chunks.

## Schema (validated by pipeline/schema.py)
```json
{ "id": "t2-c016-001",
  "source": {"book": "Tom2", "pages": [42, 43]},
  "question": "…",
  "options": {"A":"…","B":"…","C":"…","D":"…","E":"…"},
  "correct": "C", "explanation": "…" }
```
