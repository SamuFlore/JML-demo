import unittest
from pathlib import Path

from semantic_judge import SemanticDiagnosticCode, evaluate_sources


ROOT = Path(__file__).resolve().parents[3]
REFERENCE = ROOT / "Agent" / "staff" / "fixtures" / "follow_user_complete.java"
SAMPLES = ROOT / "Agent" / "exercises" / "follow_user" / "samples"


class SemanticJudgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = REFERENCE.read_text(encoding="utf-8")

    def judge(self, filename: str):
        return evaluate_sources(self.reference, (SAMPLES / filename).read_text(encoding="utf-8"))

    def test_complete_contract_passes_one_unified_evaluation(self):
        result = evaluate_sources(self.reference, self.reference)
        self.assertTrue(result.passed)
        self.assertEqual(100, result.score)
        self.assertEqual((), result.diagnostics)

    def test_missing_normal_condition_has_precise_diagnostic(self):
        result = self.judge("missing-normal-condition.java")
        self.assertFalse(result.passed)
        self.assertIn(SemanticDiagnosticCode.NORMAL_CONDITION_MISMATCH.value, {item.code for item in result.diagnostics})
        issue = next(item for item in result.diagnostics if item.code == SemanticDiagnosticCode.NORMAL_CONDITION_MISMATCH.value)
        self.assertEqual("NORMAL_CONDITION", issue.location)
        self.assertNotIn("containsUser", issue.guidance)

    def test_reversed_postconditions_are_rejected(self):
        result = self.judge("wrong-relation-direction.java")
        locations = {item.location for item in result.diagnostics}
        self.assertIn("FORWARD_POSTCONDITION", locations)
        self.assertIn("INVERSE_POSTCONDITION", locations)

    def test_overlapping_exception_conditions_are_rejected(self):
        result = self.judge("overlapping-exceptions.java")
        locations = {item.location for item in result.diagnostics}
        self.assertIn("SECOND_USER_MISSING", locations)
        self.assertIn("SELF_FOLLOW", locations)
        self.assertIn("DUPLICATE_FOLLOW", locations)

    def test_unknown_interface_symbol_is_a_format_diagnostic(self):
        result = self.judge("hallucinated-symbol.java")
        self.assertEqual(0, result.score)
        self.assertEqual("JML_FORMAT_OR_SYMBOL", result.diagnostics[0].code)

    def test_unfilled_placeholder_is_a_format_diagnostic(self):
        result = self.judge("incomplete.java")
        self.assertEqual(0, result.score)
        self.assertEqual("JML_FORMAT_OR_SYMBOL", result.diagnostics[0].code)


if __name__ == "__main__":
    unittest.main()
