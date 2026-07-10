"""Question schema and validation for the med-exam MCQ bank."""

OPTION_KEYS = ("A", "B", "C", "D", "E")


def _nonempty(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def validate_question(q: dict) -> list[str]:
    """Return a list of human-readable error strings; empty means valid."""
    errors: list[str] = []
    if not _nonempty(q.get("id")):
        errors.append("id: empty or missing")
    for field in ("question", "explanation"):
        if not _nonempty(q.get(field)):
            errors.append(f"{field}: empty or missing")
    # `topic` is optional (no topic filter in the UI); if present it must be a string.
    if "topic" in q and not isinstance(q["topic"], str):
        errors.append("topic: must be a string when present")
    opts = q.get("options")
    if not isinstance(opts, dict) or tuple(sorted(opts)) != OPTION_KEYS:
        errors.append("options: must be exactly keys A-E")
    else:
        for k in OPTION_KEYS:
            if not _nonempty(opts[k]):
                errors.append(f"option {k}: empty")
    if q.get("correct") not in OPTION_KEYS:
        errors.append("correct: must be one of A-E")
    src = q.get("source")
    if not isinstance(src, dict) or not _nonempty(src.get("book")):
        errors.append("source.book: empty or missing")
    if not isinstance(src, dict) or not isinstance(src.get("pages"), list) or not src.get("pages"):
        errors.append("source.pages: must be a non-empty list")
    return errors


def validate_bank(questions: list[dict]) -> list[str]:
    """Validate every question and flag duplicate ids."""
    errors: list[str] = []
    seen = set()
    for q in questions:
        qid = q.get("id", "<no-id>")
        for e in validate_question(q):
            errors.append(f"{qid}: {e}")
        if qid in seen:
            errors.append(f"{qid}: duplicate id")
        seen.add(qid)
    return errors
