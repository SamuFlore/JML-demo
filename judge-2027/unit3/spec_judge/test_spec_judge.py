import unittest
from pathlib import Path

from spec_judge import (
    Contract,
    SpecError,
    check_contract,
    extract_jml_block,
    follow_user_cases,
    mid_follow_user_cases,
    weak_follow_user_cases,
)


ROOT = Path(__file__).parent


class SpecJudgeTests(unittest.TestCase):
    def load(self, filename: str) -> Contract:
        source = (ROOT / "examples" / filename).read_text(encoding="utf-8")
        return Contract.parse(extract_jml_block(source, "followUser"))

    def test_correct_contract_passes_public_suite(self):
        results = check_contract(self.load("NetworkInterface_correct.java"), follow_user_cases())
        self.assertTrue(all(result.passed for result in results))

    def test_incomplete_contract_is_rejected(self):
        results = check_contract(self.load("NetworkInterface_incomplete.java"), follow_user_cases())
        failed_categories = {result.case.category for result in results if not result.passed}
        self.assertIn("精确状态更新", failed_categories)

    def test_public_suites_have_distinct_diagnostic_scope(self):
        self.assertEqual(
            ["正常转移", "双向关注关系", "双向关注关系"],
            [case.category for case in weak_follow_user_cases()],
        )
        self.assertEqual(
            ["精确状态更新", "无关用户状态保持", "修改范围"],
            [case.category for case in mid_follow_user_cases()],
        )
        self.assertEqual(6, len(follow_user_cases()))

    def test_disallows_arbitrary_java_calls(self):
        with self.assertRaises(SpecError):
            Contract.parse("assignable following(id1);\nensures Runtime.getRuntime();")

    def test_old_uses_pre_state(self):
        contract = Contract.parse(
            "assignable following(id1);\n"
            "ensures following(id1) == union(\\old(following(id1)), singleton(id2));"
        )
        results = check_contract(contract, follow_user_cases())
        self.assertTrue(results[0].ensures_actual)

    def test_overly_broad_assignable_is_rejected(self):
        contract = Contract.parse(
            "assignable following(id1), followers(id2), receivedVideos(3);\n"
            "ensures following(id1) == union(\\old(following(id1)), singleton(id2));\n"
            "ensures followers(id2) == union(\\old(followers(id2)), singleton(id1));\n"
            "ensures \\forall int u; contains(userIds(), u) && u != id1; following(u) == \\old(following(u));\n"
            "ensures \\forall int u; contains(userIds(), u) && u != id2; followers(u) == \\old(followers(u));\n"
            "ensures \\forall int u; contains(userIds(), u); receivedVideos(u) == \\old(receivedVideos(u));"
        )
        results = check_contract(contract, follow_user_cases())
        frame_case = next(result for result in results if result.case.name == "修改无关视频状态")
        self.assertFalse(frame_case.passed)
        self.assertTrue(frame_case.assignable_actual)

    def test_requires_jml_comment_before_target_method(self):
        with self.assertRaises(SpecError):
            extract_jml_block("public interface N { void followUser(int id1, int id2); }", "followUser")


if __name__ == "__main__":
    unittest.main()
