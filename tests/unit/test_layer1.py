"""First-layer reporting, process boundaries and function diagnostics on CPU."""

import json
from pathlib import Path
import resource
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import torch

from tests.fixtures.mutations import Edit
from tests.fixtures.reference import NEAR_RETURN, REFERENCE, ROOT, reference_copy
from vpmkit.candidate import check_static, load_candidate
from vpmkit.teacher import Teacher
from vpmkit.validate import VPM_PYTHON
from vpmkit.validate.check_sh import write_check_sh
from vpmkit.validate.layer1 import run_layer1
from vpmkit.validate.run_worker import check_first_state, check_state, run_candidate
from vpmkit.world import Snapshot
from .synth import snapshot


def reference_snapshot() -> Snapshot:
    state = snapshot(n=8)
    state.bodies["goal"] = state.bodies.pop("pad")
    state.contact_force = {}
    state.official = {key: torch.zeros(8) for key in
                      ("is_grasped", "is_obj_placed", "is_robot_static", "success")}
    return state


class Layer1Test(unittest.TestCase):
    def test_reference_static(self) -> None:
        report = check_static(REFERENCE)
        self.assertTrue(report.passed, report.to_markdown())
        self.assertEqual(report.problems, [])
        self.assertFalse(report.layer1_passed)

    def test_static_failure_does_not_spawn_worker(self) -> None:
        with reference_copy(Edit("notes.md", None, None)) as path, \
                patch("vpmkit.validate.layer1.subprocess.run") as run:
            report = run_layer1(path, "PickCube-v1")
        run.assert_not_called()
        self.assertEqual(report.groups["run"], "skipped")

    def test_worker_merge_and_process_settings(self) -> None:
        def worker(command: list[str], **kwargs) -> subprocess.CompletedProcess:
            self.assertEqual(command[:3], [str(VPM_PYTHON), "-m", "vpmkit.validate.run_worker"])
            self.assertEqual(kwargs["cwd"], ROOT)
            self.assertNotIn("env", kwargs)
            self.assertEqual(kwargs["timeout"], 900)
            with patch("resource.setrlimit") as limit:
                kwargs["preexec_fn"]()
                limit.assert_called_once_with(resource.RLIMIT_CORE, (0, 0))
            Path(command[-1]).write_text(json.dumps({
                "problems": [], "timing": {"total_seconds": 2.5}, "states": 744}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("vpmkit.validate.layer1.subprocess.run", side_effect=worker):
            report = run_layer1(REFERENCE, "PickCube-v1")
        self.assertTrue(report.layer1_passed)
        self.assertEqual(report.timing["run_total_seconds"], 2.5)

    def test_crash_timeout_and_missing_result_include_stderr_tail(self) -> None:
        for outcome in (subprocess.CompletedProcess([], -11, "", "omitted" + "x" * 5000 + "crashed"),
                        subprocess.TimeoutExpired([], 0.1, stderr=b"timeout evidence"),
                        subprocess.CompletedProcess([], 0, "", "missing result evidence")):
            with self.subTest(outcome=type(outcome).__name__):
                args = {"side_effect": outcome} if isinstance(outcome, Exception) else {"return_value": outcome}
                with patch("vpmkit.validate.layer1.subprocess.run", **args):
                    report = run_layer1(REFERENCE, "PickCube-v1", timeout=0.1)
                self.assertFalse(report.layer1_passed)
                self.assertEqual(report.groups["run"], "failed")
                self.assertEqual([p.code for p in report.problems], ["run.error"])
                message = report.problems[0].message
                self.assertIn("Worker stderr (tail):", message)
                self.assertNotIn("omitted", message)
                self.assertIn("evidence" if "evidence" in str(outcome.stderr) else "crashed", message)

    def test_script_render_and_argument_rejection_before_python(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workspace with spaces ") as folder:
            with patch("vpmkit.validate.check_sh.VPM_PYTHON", Path("/nonexistent/python")):
                script = write_check_sh(folder, "PickCube-v1")
            source = script.read_text(encoding="utf-8")
            self.assertNotRegex(source, r"@[A-Z_]+@")
            self.assertEqual(script.stat().st_mode & 0o777, 0o755)
            result = subprocess.run([str(script), "argument"], env={}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stderr.strip(), "check.sh takes no arguments")

    def test_cli_usage_static_failure_json_and_internal_error_from_another_directory(self) -> None:
        with reference_copy(Edit("notes.md", None, None)) as path:
            command = [str(VPM_PYTHON), str(ROOT / "scripts/check_candidate.py")]
            result = subprocess.run(command, cwd=path.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            output = path.parent / "report.json"
            result = subprocess.run(command + ["--env", "PickCube-v1", "--json", str(output), str(path)],
                                    cwd=path.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("parse.missing_file", result.stdout)
            self.assertEqual(json.loads(output.read_text())["groups"]["run"], "skipped")
            result = subprocess.run(command + ["--env", "PickCube-v1", "--json", str(path), str(path)],
                                    cwd=path.parent, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("IsADirectoryError", result.stderr)


class WorkerTest(unittest.TestCase):
    def test_all_resets_actions_and_states_use_one_environment(self) -> None:
        env = Mock()
        env.unwrapped.device = torch.device("cpu")
        adapter = Mock()
        adapter.snapshot.return_value = reference_snapshot()
        with patch("vpmkit.adapters.maniskill.make_env", return_value=env) as make, \
                patch("vpmkit.adapters.maniskill.ManiSkillAdapter", return_value=adapter) as bind:
            result = run_candidate(REFERENCE, "PickCube-v1")
        self.assertEqual(result["problems"], [])
        self.assertEqual(result["states"], 744)
        make.assert_called_once_with("PickCube-v1", num_envs=8)
        bind.assert_called_once()
        self.assertEqual([call.kwargs for call in env.reset.call_args_list],
                         [{"seed": 0}, {"seed": 1}, {"seed": 2}])
        self.assertEqual([call.args for call in env.action_space.seed.call_args_list], [(0,), (1,), (2,)])
        self.assertEqual(env.step.call_count, 90)
        self.assertEqual(env.action_space.sample.call_count, 90)
        self.assertEqual(adapter.snapshot.call_count, 93)
        env.close.assert_called_once()

    def test_first_snapshot_exception_is_binding_error(self) -> None:
        env = Mock()
        with patch("vpmkit.adapters.maniskill.make_env", return_value=env), \
                patch("vpmkit.adapters.maniskill.ManiSkillAdapter") as adapter:
            adapter.return_value.snapshot.side_effect = ValueError("snapshot failed")
            result = run_candidate(REFERENCE, "PickCube-v1")
        self.assertEqual([p["code"] for p in result["problems"]], ["run.bind"])
        self.assertIn("ValueError: snapshot failed", result["problems"][0]["message"])
        env.close.assert_called_once()

    def test_candidate_traceback_uses_innermost_helper_and_omits_runtime(self) -> None:
        with reference_copy(Edit("predicates.py", "return torch.linalg.norm(g.pos - o.pos, dim=-1)",
                                 "return g.missing")) as path:
            teacher = Teacher(load_candidate(path), num_envs=8)
            problems = check_first_state(teacher, reference_snapshot())
            line = next(i for i, text in enumerate((path / "predicates.py").read_text().splitlines(), 1)
                        if "return g.missing" in text)
        self.assertEqual(len(problems), 2)
        for problem in problems:
            self.assertEqual(problem.code, "run.error")
            self.assertEqual(problem.location, f"predicates.py:{line}")
            self.assertIn("AttributeError", problem.message)
            self.assertIn("return g.missing", problem.message)
            self.assertNotIn("teacher.py:", problem.message)
            self.assertIn("seed=0, step=0", problem.message)
        self.assertIn("progress.py:", problems[1].message)

    def test_nonfinite_margin_and_default_progress_are_both_reported(self) -> None:
        with reference_copy(Edit("predicates.py", "return max_dist - torch.linalg.norm(t.pos - o.pos, dim=-1)",
                                 'return torch.full((w.batch_size,), float("nan"), device=w.device)')) as path:
            teacher = Teacher(load_candidate(path), num_envs=8)
            problems = check_first_state(teacher, reference_snapshot())
        self.assertEqual([(p.code, p.location) for p in problems],
                         [("run.nonfinite", "at_goal(cube, goal)"),
                          ("run.nonfinite", "default progress of carry")])

    def test_progress_failure_is_checked_when_a_predicate_also_fails(self) -> None:
        with reference_copy(Edit("predicates.py", NEAR_RETURN, "return g.pos"),
                            Edit("progress.py", "return 1.0 - tcp_dist(w, o.g, o.cube) / d0",
                                 "return o.g.pos")) as path:
            problems = check_first_state(Teacher(load_candidate(path), num_envs=8), reference_snapshot())
        self.assertEqual([(p.code, p.location) for p in problems],
                         [("run.output", "near(g, cube)"), ("run.output", "progress_reach")])

    def test_later_failure_stops_at_first_function_and_identifies_step(self) -> None:
        with reference_copy(Edit("predicates.py", NEAR_RETURN,
                                 "return g.pos if g.pos[0, 0] > 0 else radius + max_dist - tcp_dist(w, g, o)")) as path:
            teacher = Teacher(load_candidate(path), num_envs=8)
            state = reference_snapshot()
            self.assertEqual(check_first_state(teacher, state), [])
            state.bodies["g"].pose[:, 0] = 1
            problem = check_state(teacher, state, 2, 7)
        self.assertEqual(problem.code, "run.output")
        self.assertEqual(problem.location, "near(g, cube)")
        self.assertIn("seed=2, step=7", problem.message)

    def test_stage_update_exception_is_run_error(self) -> None:
        teacher = Teacher(load_candidate(REFERENCE), num_envs=8)
        with patch.object(teacher._automaton, "step", side_effect=ValueError("stage update failed")):
            problem = check_state(teacher, reference_snapshot(), 1, 4)
        self.assertEqual(problem.code, "run.error")
        self.assertEqual(problem.location, "Teacher.step")
        self.assertIn("ValueError: stage update failed", problem.message)
