import unittest
from pipeline.schema import validate_question, validate_bank

def good():
    return {
        "id": "t2-ch09-001", "topic": "Zatoki",
        "source": {"book": "Tom2", "pages": [10, 12]},
        "question": "Pytanie?",
        "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        "correct": "C", "explanation": "Bo tak.",
    }

class TestValidateQuestion(unittest.TestCase):
    def test_good_question_has_no_errors(self):
        self.assertEqual(validate_question(good()), [])

    def test_missing_option_flagged(self):
        q = good(); del q["options"]["E"]
        self.assertTrue(any("option" in e.lower() for e in validate_question(q)))

    def test_bad_correct_flagged(self):
        q = good(); q["correct"] = "F"
        self.assertTrue(any("correct" in e.lower() for e in validate_question(q)))

    def test_empty_field_flagged(self):
        q = good(); q["question"] = "  "
        self.assertTrue(any("question" in e.lower() for e in validate_question(q)))

    def test_empty_pages_flagged(self):
        q = good(); q["source"]["pages"] = []
        self.assertTrue(any("pages" in e.lower() for e in validate_question(q)))

class TestValidateBank(unittest.TestCase):
    def test_duplicate_ids_flagged(self):
        a, b = good(), good()
        errs = validate_bank([a, b])
        self.assertTrue(any("duplicate" in e.lower() for e in errs))
