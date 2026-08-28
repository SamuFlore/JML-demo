import tempfile
import unittest
from pathlib import Path

from hw9_agent.critic import analyze
from hw9_agent.client import ModelClientError, extract_chat_content, extract_output_text
from hw9_agent.parser import parse_interface
from hw9_agent.pipeline import run_pipeline
from hw9_agent.exercise import ExerciseBundle, deterministic_check
from hw9_agent.webapp import ExerciseWebApp


FIXTURE = r"""
public interface DemoInterface {
    //@ ensures \result == value;
    public /*@ pure @*/ int getValue();

    /*@ public normal_behavior
      @ requires value >= 0;
      @ assignable items;
      @ ensures items.length == \old(items.length) + 1;
      @ also
      @ public exceptional_behavior
      @ signals (IllegalArgumentException e) value < 0;
      @*/
    public /*@ safe @*/ void add(int value);
}
"""


class AgentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "DemoInterface.java"
        self.path.write_text(FIXTURE, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_parses_single_and_block_specs(self):
        interface = parse_interface(self.path)
        self.assertEqual(["getValue", "add"], [m.name for m in interface.methods])
        self.assertEqual(["pure"], interface.methods[0].markers)
        self.assertEqual(["value >= 0"], interface.methods[1].requires)
        self.assertEqual(1, len(interface.methods[1].signals))

    def test_pure_method_creates_side_effect_obligation(self):
        method = parse_interface(self.path).methods[0]
        result = analyze(method)
        self.assertTrue(any("状态必须完全一致" in item for item in result.test_obligations))

    def test_extracts_responses_api_output_text(self):
        payload = {
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": "hello"}],
            }]
        }
        self.assertEqual("hello", extract_output_text(payload))
        with self.assertRaises(ModelClientError):
            extract_output_text({"output": []})

    def test_extracts_deepseek_chat_content(self):
        payload = {"choices": [{"message": {"content": "demo"}}]}
        self.assertEqual("demo", extract_chat_content(payload))
        with self.assertRaises(ModelClientError):
            extract_chat_content({"choices": []})

    def test_four_stage_pipeline_with_fake_model(self):
        root = Path(self.temp.name)
        official = root / "official" / "com" / "oocourse" / "spec1" / "main"
        official.mkdir(parents=True)
        (official / "NetworkInterface.java").write_text(
            """public interface NetworkInterface {
            //@ ensures \\result == true;
            public /*@ pure @*/ boolean followUser(int id1, int id2);
            }""",
            encoding="utf-8",
        )
        for name in ("UserInterface", "VideoInterface"):
            (official / f"{name}.java").write_text(
                f"public interface {name} {{}}", encoding="utf-8"
            )
        case_dir = root / "case"
        case_dir.mkdir()
        (case_dir / "requirement.md").write_text("demo", encoding="utf-8")
        project_root = Path(__file__).resolve().parent.parent

        class FakeClient:
            def __init__(self):
                self.count = 0

            def generate(self, prompt):
                self.count += 1
                self.last_prompt = prompt
                return f"stage-{self.count}"

        fake = FakeClient()
        result = run_pipeline(
            client=fake,
            project_root=project_root,
            source_root=str(root),
            case_dir=case_dir,
            output_dir=root / "run",
            method_name="followUser",
        )
        self.assertEqual(4, fake.count)
        self.assertEqual({"analyzer", "planner", "generator", "critic"}, set(result.artifacts))
        self.assertIn("Prior artifact: spec.jml", fake.last_prompt)

    def test_exercise_detects_unfilled_blank(self):
        project_root = Path(__file__).resolve().parent.parent
        bundle = ExerciseBundle.load(project_root / "exercises" / "follow_user")
        submission = (
            project_root / "exercises" / "follow_user" / "samples" / "incomplete.jml"
        ).read_text(encoding="utf-8")
        findings = deterministic_check(bundle, submission)
        self.assertTrue(any(item["code"] == "UNFILLED_BLANKS" for item in findings))

    def test_exercise_accepts_complete_structure_for_semantic_review(self):
        project_root = Path(__file__).resolve().parent.parent
        bundle = ExerciseBundle.load(project_root / "exercises" / "follow_user")
        submission = (
            project_root / "exercises" / "follow_user" / "samples" / "complete.jml"
        ).read_text(encoding="utf-8")
        findings = deterministic_check(bundle, submission)
        self.assertEqual(["STRUCTURE_OK"], [item["code"] for item in findings])

    def test_web_payload_does_not_expose_hidden_rubric(self):
        project_root = Path(__file__).resolve().parent.parent
        app = ExerciseWebApp(
            project_root=project_root,
            source_root="unused-for-public-payload",
            exercise_dir=project_root / "exercises" / "follow_user",
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
        )
        payload = app.public_exercise()
        self.assertNotIn("rubric", payload)
        self.assertNotIn("criteria", payload)
        self.assertIn("template", payload)


if __name__ == "__main__":
    unittest.main()
