"""Review output contracts and feedback formatting."""

from dataclasses import asdict
import json
import unittest

from vpmkit.harness.review import ReviewItem, ReviewParseError, parse_review, render_review, review_prompt


class ReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.item = ReviewItem("a", "error", "candidate/predicates.py:23",
                               "Threshold differs from evaluate().", "Use the official threshold.")

    def test_array_and_fenced_array(self) -> None:
        text = json.dumps([asdict(self.item)])
        for source in (text, f"```json\n{text}\n```", f"\n```json\n{text}\n```\n"):
            with self.subTest(source=source):
                self.assertEqual(parse_review(source), [self.item])
        self.assertEqual(parse_review("[]"), [])

    def test_array_and_fenced_block_inside_prose(self) -> None:
        text = json.dumps([asdict(self.item)])
        for source in (f"The review found these problems: {text}\nEnd of review.",
                       f"The review found these problems:\n```json\n{text}\n```\nEnd of review.",
                       f"See [context].\n```json\n{text}\n```\nEnd [review]."):
            with self.subTest(source=source):
                self.assertEqual(parse_review(source), [self.item])
        self.assertEqual(parse_review("No findings: [] End of review."), [])

    def test_invalid_fence_falls_back_to_array(self) -> None:
        self.assertEqual(parse_review("```json\n{}\n```\nFindings: []"), [])

    def test_invalid_review_is_a_harness_error(self) -> None:
        missing = asdict(self.item)
        del missing["fix"]
        cases = ["not JSON", "{}", "[null]", json.dumps([missing]),
                 "Findings: [not JSON] End of review.", "```json\n{}\n```",
                 f"Findings: {json.dumps([missing])} End of review.",
                 f"Findings:\n```json\n{json.dumps([missing])}\n```\nEnd of review.",
                 json.dumps([{**asdict(self.item), "location": 23}]),
                 json.dumps([{**asdict(self.item), "category": "k"}]),
                 json.dumps([{**asdict(self.item), "severity": "warning"}])]
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ReviewParseError):
                parse_review(source)

    def test_severity_contract_and_correction_note(self) -> None:
        for category in "abcdefghij":
            for severity in ("error", "reminder"):
                with self.subTest(category=category, severity=severity):
                    item = parse_review(json.dumps([
                        {**asdict(self.item), "category": category, "severity": severity}]))[0]
                    corrected = category in "fghij" and severity == "error"
                    self.assertEqual(item.severity, "reminder" if corrected else severity)
                    self.assertEqual(bool(item.note), corrected)

    def test_prompt_substitution_and_previous_errors_only(self) -> None:
        reminder = ReviewItem("g", "reminder", "notes.md", "Reminder only", "Improve wording")
        first = review_prompt("PickCube-v1", "First-layer report", [])
        for placeholder in ("{env_id}", "{layer1_report}", "{previous_review}"):
            self.assertNotIn(placeholder, first)
        self.assertIn("PickCube-v1", first)
        self.assertIn("First-layer report", first)
        self.assertNotIn("The previous review reported these errors:", first)
        second = review_prompt("PickCube-v1", "Report with {previous_review} literal", [self.item, reminder])
        self.assertIn("The previous review reported these errors:", second)
        self.assertIn(self.item.problem, second)
        self.assertNotIn(reminder.problem, second)
        self.assertIn("Report with {previous_review} literal", second)

    def test_render_errors_before_reminders_with_all_fields(self) -> None:
        reminder = ReviewItem("f", "reminder", "stages[1]", "Merge stages", "Combine guards")
        rendered = render_review([reminder, self.item])
        self.assertLess(rendered.index(self.item.problem), rendered.index(reminder.problem))
        for value in ("a. official", "f. granularity", self.item.location, self.item.fix,
                      reminder.location, reminder.fix):
            self.assertIn(value, rendered)
