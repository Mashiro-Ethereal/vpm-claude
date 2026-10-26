"""Scripted generation and review with real, isolated first-layer GPU checks."""

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from tests.fixtures.harness import harness_config
from tests.fixtures.reference import REFERENCE
from vpmkit.harness.backends import ScriptedBackend
from vpmkit.harness.run import run_generation


@unittest.skipUnless(os.environ.get("VPM_INTEGRATION") == "1", "set VPM_INTEGRATION=1")
class HarnessIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="harness-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = harness_config(self.root / "runs")
        self.assertEqual(os.environ.get("CUDA_VISIBLE_DEVICES"), "1")

    def broken_candidate(self) -> Path:
        broken = self.root / "broken"
        shutil.copytree(REFERENCE, broken)
        (broken / "notes.md").unlink()
        return broken

    def test_reference_passes_in_one_round_with_records(self) -> None:
        verdict = run_generation("PickCube-v1", ScriptedBackend([REFERENCE], ["[]"]), self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 1), verdict.to_json())
        records = verdict.run_dir / "records"
        self.assertEqual({path.name for path in records.iterdir()}, {"run.json", "verdict.json", "round_1"})
        round_dir = records / "round_1"
        for name in ("prompt.txt", "generation.jsonl", "generation.stderr.txt", "generation_result.json",
                     "candidate/notes.md", "layer1.json", "layer1.md", "review_prompt.txt", "review.jsonl",
                     "review.stderr.txt", "review_call.json", "review.json", "review.md", "round.json"):
            self.assertTrue((round_dir / name).exists(), name)
        self.assertEqual((round_dir / "prompt.txt").read_text(), "Read TASK.md first.")
        self.assertEqual(json.loads((round_dir / "layer1.json").read_text())["groups"]["run"], "passed")
        self.assertEqual(json.loads((round_dir / "review.json").read_text()), [])

    def test_layer1_failure_then_reference(self) -> None:
        backend = ScriptedBackend([self.broken_candidate(), REFERENCE])
        verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 2), verdict.to_json())
        records = verdict.run_dir / "records"
        self.assertIn("parse.missing_file", (records / "round_2/prompt.txt").read_text())
        self.assertFalse((records / "round_1/review.jsonl").exists())

    def test_review_error_then_clean_review(self) -> None:
        error = {"category": "a", "severity": "error", "location": "candidate/predicates.py:23",
                 "problem": "Scripted official mismatch", "fix": "Match evaluate()"}
        backend = ScriptedBackend([REFERENCE, REFERENCE], [json.dumps([error]), "[]"])
        verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 2), verdict.to_json())
        second = verdict.run_dir / "records/round_2"
        self.assertIn("a. official", (second / "prompt.txt").read_text())
        self.assertIn(error["problem"], (second / "prompt.txt").read_text())
        self.assertIn(error["problem"], (second / "review_prompt.txt").read_text())
        self.assertEqual(verdict.rounds[0]["review_error_categories"], {"a": 1})

    def test_all_four_rounds_fail_layer1(self) -> None:
        backend = ScriptedBackend([self.broken_candidate()] * 4)
        verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("failed", 4), verdict.to_json())
        self.assertTrue(all(summary["layer1_codes"] == {"parse.missing_file": 1} for summary in verdict.rounds))
        self.assertTrue(all(not summary["review_attempts"] for summary in verdict.rounds))

    def test_three_non_json_reviews_are_harness_failure(self) -> None:
        backend = ScriptedBackend([REFERENCE], ["not JSON"] * 3)
        verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("harness_failure", 1), verdict.to_json())
        self.assertEqual(len(verdict.rounds[0]["review_attempts"]), 3)
        self.assertEqual(len(verdict.rounds[0]["generation_attempts"]), 1)
