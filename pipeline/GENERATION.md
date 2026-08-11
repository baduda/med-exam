# Generation protocol (agent-run)

Questions are generated **by the Claude Code agent in-session** (no Anthropic
API key). Work is resumable via `data/state.json` (`generated` flag per chunk).

## Per chunk
1. Read `data/chunks/<chunk_id>.json` → `{chunk_id, book, pages, text}`.
2. **Skip junk chunks** — if the text is mostly table-of-contents (dot-leader
   runs `.....`), a bibliography/`Piśmiennictwo` list of "Author A., Author B.:"
   citations, or OCR garble with few full Polish sentences, skip it (mark
   `generated: true`, write no questions). Only generate from real prose.
   **Also skip historical and institutional chapters** — who headed which
   department in which years, who is "ojcem polskiej stomatologii", who is the
   current national consultant. It reads as prose but yields pure trivia that
   tests nothing a candidate is examined on. Rule of thumb: if the answer is a
   person, a city or a year, it does not belong in the bank.
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

## Extra styles (wave 4+): combined and clinical questions

Two additional question styles enrich the bank. Both stay single-select (one
letter A–E correct) and use the SAME schema, plus an optional `"type"` field.

### combined  (`"type": "combined"`)
Numbered statements embedded in `question`, options are combinations. Example:
```
"question": "Wskaż prawdziwe stwierdzenia dotyczące kostniwiaka (cementoblastoma):\n1. Rozwija się głównie przed 30. r.ż.\n2. Najczęściej dotyczy górnych siekaczy.\n3. Pierwszym objawem jest zwykle ból zęba.\n4. Jest ściśle związany z korzeniem zęba.",
"options": {"A":"tylko 1 i 2","B":"tylko 1, 3 i 4","C":"tylko 2 i 4","D":"wszystkie prawidłowe","E":"żadna z powyższych"},
"correct": "B"
```
CRITICAL: craft the four statements and the five combination-options so that
**exactly one** option correctly names all-and-only the true statements. Double-
check which statements are true against the chunk before choosing `correct`.

### clinical  (`"type": "clinical"`)
A short patient vignette, then a decision. Example:
```
"question": "Do gabinetu zgłasza się 10-letni pacjent 40 minut po urazie z całkowicie wybitym stałym zębem siecznym; ząb przyniesiono w mleku. Jakie postępowanie jest właściwe?",
"options": {"A":"…","B":"…","C":"…","D":"…","E":"…"}, "correct":"C"
```
Ground the vignette + correct management strictly in the chunk's content.

Both: still Polish, 5 options A–E similar length, one correct, real `source.pages`.

## Schema (validated by pipeline/schema.py)
```json
{ "id": "t2-c016-001",
  "source": {"book": "Tom2", "pages": [42, 43]},
  "question": "…",
  "options": {"A":"…","B":"…","C":"…","D":"…","E":"…"},
  "correct": "C", "explanation": "…" }
```
