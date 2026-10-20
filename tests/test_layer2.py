import json
from pathlib import Path
import tempfile
import unittest

from tests import TOY
from vpmkit.validate.layer2 import ScriptedReviewBackend, build_review_prompt, parse_review, run_layer2
from vpmkit.validate.report import CheckResult, Layer1Report


class Layer2Tests(unittest.TestCase):
    def test_bare_and_fenced_json(self):
        bare = '{"verdict": "pass", "issues": []}'
        for text in (bare, f"Here is the review:\n```json\n{bare}\n```\n", f"Notes {{informal}}\n{bare}"):
            report = parse_review(text)
            self.assertTrue(report.parse_ok)
            self.assertEqual(report.verdict, "pass")
            self.assertEqual(report.raw_text, text)

    def test_garbage_and_invalid_schema(self):
        for text in ("garbage", "{}", '{"verdict":"maybe","issues":[]}',
                     '{"verdict":"fail","issues":[]}', '{"verdict":"pass","issues":[{}]}',
                     '{"verdict":"pass","issues":{}}'):
            with self.subTest(text=text):
                report = parse_review(text)
                self.assertFalse(report.parse_ok)
                self.assertEqual(report.verdict, "fail")
                self.assertEqual(report.issues[0].severity, "error")
                self.assertEqual(report.issues[0].location, "review.unparseable")

    def test_pass_with_errors_and_warnings(self):
        data = {"verdict": "pass", "issues": [{"severity": "error", "location": "carry",
                "problem": "Regression target requires opening a held object", "suggestion": "Target grasp"}]}
        report = parse_review(json.dumps(data))
        self.assertTrue(report.parse_ok)
        self.assertEqual(report.verdict, "fail")
        data["issues"][0]["severity"] = "warning"
        self.assertEqual(parse_review(json.dumps(data)).verdict, "pass")

    def test_prompt_embeds_sources_and_scripted_backend_order(self):
        layer1 = Layer1Report(str(TOY), "Toy-v1", True, [CheckResult("run", "pass")], None, "start", "end")
        summary = {"trajectories": [], "aggregate": {"num_trajectories": 0}}
        prompt = build_review_prompt("Move the block", "def evaluate(): return success", TOY, layer1, summary)
        self.assertIn("Move the block", prompt)
        self.assertIn("def evaluate(): return success", prompt)
        self.assertIn(layer1.to_markdown(), prompt)
        self.assertIn(json.dumps(summary, indent=2), prompt)
        for path in TOY.iterdir():
            if path.is_file():
                self.assertIn(path.read_text(), prompt)
        self.assertIn("open gripper while the object is still held", prompt)
        backend = ScriptedReviewBackend(['{"verdict":"pass","issues":[]}', "garbage"])
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(run_layer2(backend, "task", "source", TOY, layer1, summary, Path(temp)).verdict, "pass")
            self.assertFalse(run_layer2(backend, "task", "source", TOY, layer1, summary, Path(temp)).parse_ok)
        with self.assertRaises(StopIteration):
            backend.review("prompt", Path("."))


if __name__ == "__main__":
    unittest.main()
