"""Run layout, repair flow, retries and durable records without GPU workers."""

from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.fixtures.harness import harness_config, small_package
from tests.fixtures.reference import REFERENCE
from vpmkit.candidate import Problem, Report
from vpmkit.harness.backends import ReviewCall, RoundResult, ScriptedBackend
from vpmkit.harness.rundir import create_run
from vpmkit.harness.run import run_generation


def passed_report() -> Report:
    return Report("candidate", dict.fromkeys(("parse", "schema", "ast", "run"), "passed"), [])


class HarnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = small_package(self.root)
        self.config = harness_config(self.root / "runs")
        self.config["paths"]["packages"] = str(self.package.parent)

    def test_workspace_permissions_git_and_collision_suffix(self) -> None:
        with patch("vpmkit.harness.rundir.datetime") as clock:
            clock.now.return_value = datetime(2026, 10, 26, 12, 34, 56)
            first = create_run(self.package, self.root / "runs", "PickCube-v1", 1)
            second = create_run(self.package, self.root / "runs", "PickCube-v1", 1)
        self.assertEqual(first.path.name, "20261026-123456")
        self.assertEqual(second.path.name, "20261026-123456-1")
        self.assertEqual(first.path.parent.name, "PickCube-v1")
        for original in self.package.rglob("*"):
            target = first.workspace / original.relative_to(self.package)
            self.assertEqual(target.stat().st_mode & 0o777, 0o555 if original.is_dir() else 0o444)
            if original.is_file():
                self.assertEqual(original.read_bytes(), target.read_bytes())
        self.assertTrue((first.workspace / ".git").is_dir())
        self.assertEqual((first.workspace / "check.sh").stat().st_mode & 0o777, 0o555)
        self.assertTrue(os.access(first.workspace, os.W_OK))
        candidate = first.workspace / "candidate"
        self.assertEqual(list(candidate.iterdir()), [])
        (candidate / "write-test").write_text("writable")
        self.assertTrue(first.records.is_dir())
        self.assertFalse(first.records.is_relative_to(first.workspace))

    def test_one_round_records_snapshot_and_reminders_pass(self) -> None:
        review = json.dumps([{"category": "f", "severity": "error", "location": "stages[0]",
                              "problem": "Could merge", "fix": "Merge stages"}])
        backend = ScriptedBackend([REFERENCE], [review])

        def check(candidate: Path, env_id: str) -> Report:
            (candidate / "created-by-check").write_text("after snapshot")
            return passed_report()

        with patch("vpmkit.harness.run.run_layer1", side_effect=check):
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 1))
        records = verdict.run_dir / "records"
        round_dir = records / "round_1"
        self.assertEqual((round_dir / "prompt.txt").read_text(), "Read TASK.md first.")
        expected = {"prompt.txt", "generation.jsonl", "generation.stderr.txt", "generation_result.json",
                    "candidate", "layer1.json", "layer1.md", "review_prompt.txt", "review.jsonl",
                    "review.stderr.txt", "review_call.json", "review.json", "review.md", "round.json"}
        self.assertEqual({path.name for path in round_dir.iterdir()}, expected)
        self.assertFalse((round_dir / "candidate/created-by-check").exists())
        self.assertEqual((round_dir / "candidate/notes.md").read_bytes(), (REFERENCE / "notes.md").read_bytes())
        item = json.loads((round_dir / "review.json").read_text())[0]
        self.assertEqual(item["severity"], "reminder")
        self.assertTrue(item["note"])
        metadata = json.loads((records / "run.json").read_text())
        self.assertEqual(metadata["package_sha256"], "package-hash-from-manifest")
        self.assertIsInstance(metadata["environment_names"], list)
        self.assertEqual(metadata["config"], self.config)
        self.assertIsNone(metadata["cli_version"])
        self.assertTrue(metadata["session_id"])
        self.assertLessEqual(metadata["started_at"], metadata["ended_at"])
        self.assertEqual(json.loads((records / "verdict.json").read_text()), json.loads(verdict.to_json()))

    def test_layer1_passed_property_controls_review(self) -> None:
        report = passed_report()
        report.groups["run"] = "skipped"
        self.assertTrue(report.passed)
        backend = ScriptedBackend([REFERENCE] * 4)
        backend.review = Mock(side_effect=AssertionError("Must skip review"))
        with patch("vpmkit.harness.run.run_layer1", return_value=report):
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("failed", 4))
        backend.review.assert_not_called()

    def test_generation_retry_resumes_same_prompt_and_preserves_attempts(self) -> None:
        backend = ScriptedBackend([
            RoundResult("error", session_id="session-kept", exit_code=1, check_sh_calls=2),
            RoundResult("error", exit_code=1, check_sh_calls=1), REFERENCE])
        backend.generate = Mock(wraps=backend.generate)
        with patch("vpmkit.harness.run.run_layer1", return_value=passed_report()) as check:
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 1))
        self.assertEqual([call.args[2] for call in backend.generate.call_args_list],
                         [None, "session-kept", "session-kept"])
        self.assertEqual({call.args[1] for call in backend.generate.call_args_list}, {"Read TASK.md first."})
        check.assert_called_once()
        summary = verdict.rounds[0]
        self.assertEqual(summary["check_sh_calls"], 3)
        self.assertEqual([item["outcome"] for item in summary["generation_attempts"]],
                         ["error", "error", "completed"])
        for subdir in (".", "generation_retry_1", "generation_retry_2"):
            self.assertTrue((verdict.run_dir / "records/round_1" / subdir / "generation.jsonl").exists())

    def test_exhausted_generation_retries_stop_before_checks(self) -> None:
        backend = ScriptedBackend([RuntimeError("backend unavailable")] * 3)
        with patch("vpmkit.harness.run.run_layer1") as check:
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("harness_failure", 1))
        self.assertEqual(len(verdict.rounds[0]["generation_attempts"]), 3)
        self.assertIn("backend unavailable", verdict.error)
        check.assert_not_called()

    def test_max_turns_and_timeout_are_checked_then_repaired_in_same_session(self) -> None:
        for outcome in ("max_turns", "timeout"):
            backend = ScriptedBackend([RoundResult(outcome, session_id="continue-this"), REFERENCE])
            backend.generate = Mock(wraps=backend.generate)
            failed = Report("candidate", {"parse": "failed", "schema": "skipped", "ast": "skipped", "run": "skipped"},
                            [Problem("parse.missing_file", "notes.md", "Missing notes.md")])
            with patch("vpmkit.harness.run.run_layer1", side_effect=[failed, passed_report()]):
                verdict = run_generation("PickCube-v1", backend, self.config)
            self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 2))
            second_call = backend.generate.call_args_list[1]
            self.assertEqual(second_call.args[2], "continue-this")
            self.assertTrue(second_call.args[1].startswith("The checks after round 1 found problems in candidate/."))
            self.assertIn("parse.missing_file", second_call.args[1])
            self.assertEqual(verdict.rounds[0]["layer1_codes"], {"parse.missing_file": 1})

    def test_review_failure_retries_only_review_and_keeps_generator_session(self) -> None:
        error = {"category": "a", "severity": "error", "location": "predicates.py:23",
                 "problem": "Wrong official threshold", "fix": "Use 0.025"}
        backend = ScriptedBackend([REFERENCE, REFERENCE], [
            RuntimeError("API failed"), ReviewCall("timeout", timed_out=True),
            json.dumps([error, error]), "[]"])
        backend.generate = Mock(wraps=backend.generate)
        with patch("vpmkit.harness.run.run_layer1", return_value=passed_report()) as check:
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 2))
        self.assertEqual(check.call_count, 2)
        self.assertEqual(len(verdict.rounds[0]["review_attempts"]), 3)
        self.assertEqual(verdict.rounds[0]["review_error_categories"], {"a": 2})
        second = verdict.run_dir / "records/round_2"
        repair = (second / "prompt.txt").read_text()
        self.assertIn("a. official", repair)
        self.assertIn(error["problem"], repair)
        self.assertIn("Responses to review", repair)
        self.assertIn(error["problem"], (second / "review_prompt.txt").read_text())
        self.assertTrue(backend.generate.call_args_list[1].args[2].startswith("scripted-"))

    def test_parse_failure_retry_keeps_raw_output(self) -> None:
        backend = ScriptedBackend([REFERENCE], ["not JSON", "[]"])
        with patch("vpmkit.harness.run.run_layer1", return_value=passed_report()) as check:
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual(verdict.status, "passed")
        check.assert_called_once()
        self.assertIn("Invalid review JSON", verdict.rounds[0]["review_attempts"][0]["error"])
        original = verdict.run_dir / "records/round_1/review.jsonl"
        self.assertIn("not JSON", original.read_text())

    def test_review_errors_survive_an_intervening_layer1_failure(self) -> None:
        error = {"category": "a", "severity": "error", "location": "predicates.py:23",
                 "problem": "Wrong official threshold", "fix": "Use 0.025"}
        backend = ScriptedBackend([REFERENCE] * 3, [json.dumps([error]), "[]"])
        failed = Report("candidate", {"parse": "failed", "schema": "skipped", "ast": "skipped", "run": "skipped"},
                        [Problem("parse.missing_file", "notes.md", "Missing notes.md")])
        with patch("vpmkit.harness.run.run_layer1", side_effect=[passed_report(), failed, passed_report()]):
            verdict = run_generation("PickCube-v1", backend, self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("passed", 3))
        records = verdict.run_dir / "records"
        self.assertFalse((records / "round_2/review_prompt.txt").exists())
        prompt = (records / "round_3/review_prompt.txt").read_text()
        self.assertIn("The previous review reported these errors:", prompt)
        for field in ("location", "problem", "fix"):
            self.assertIn(error[field], prompt)
        self.assertEqual(verdict.rounds[2]["review_error_categories"], {})

    def test_non_json_three_times_is_harness_failure(self) -> None:
        with patch("vpmkit.harness.run.run_layer1", return_value=passed_report()):
            verdict = run_generation("PickCube-v1", ScriptedBackend([REFERENCE], ["not JSON"] * 3), self.config)
        self.assertEqual((verdict.status, verdict.rounds_used), ("harness_failure", 1))
        self.assertEqual(len(verdict.rounds[0]["review_attempts"]), 3)

    def test_supplied_run_and_callable_candidate(self) -> None:
        run = create_run(self.package, self.root / "runs", "PickCube-v1", 1)

        def write_candidate(candidate: Path) -> None:
            self.assertEqual(list(candidate.iterdir()), [])
            (candidate / "notes.md").write_text("scripted function")

        backend = ScriptedBackend([write_candidate])
        with patch("vpmkit.harness.run.run_layer1", return_value=passed_report()):
            verdict = run_generation("PickCube-v1", backend, self.config, run=run)
        self.assertEqual(verdict.run_dir, run.path)
        self.assertEqual((run.records / "round_1/candidate/notes.md").read_text(), "scripted function")
