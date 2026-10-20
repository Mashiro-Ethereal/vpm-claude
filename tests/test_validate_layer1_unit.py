from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import torch

from tests import TOY, world
from vpmkit.artifact.loader import load_candidate
from vpmkit.artifact.schema import Issue
from vpmkit.runtime.teacher import Teacher
from vpmkit.validate.layer1 import _run_frames, official_agreement, trajectory_checks, validate_layer1
from vpmkit.validate.replay import Trajectory
from vpmkit.validate.report import CheckResult, Layer1Report
from vpmkit.world import WorldState


def successful_trajectory():
    frames = [world(block_x=0.2, width=0.02), world(block_x=0.05),
              world(block_x=0.05, held=True, width=0.02),
              world(block_x=0.6, held=True, width=0.02),
              world(block_x=1., held=True, width=0.02), world(block_x=1.)]
    states = WorldState.cat(frames)
    states.official["success"][-1] = True
    return Trajectory(states, True, "synthetic success")


class Layer1UnitTests(unittest.TestCase):
    def setUp(self):
        self.candidate = load_candidate(TOY)
        self.teacher = Teacher(self.candidate, 1)

    def test_official_pass_fail_and_uncovered(self):
        traj = successful_trajectory()
        check = official_agreement(self.teacher, [traj.states])
        self.assertEqual(check.status, "pass")
        self.assertEqual(check.stats["entries"][0]["agreement"], 1.0)
        self.assertEqual(check.stats["entries"][0]["num_states"], 6)
        # Negated grasped is essential: at-goal while held is not official success.
        traj.states.official["success"][4] = True
        check = official_agreement(self.teacher, [traj.states])
        self.assertEqual(check.status, "fail")
        mismatch = check.stats["entries"][0]["mismatches"][0]
        self.assertEqual(mismatch["row"], 4)
        self.assertEqual(mismatch["margins"]["not grasped(g, block)"], 1.0)
        check = official_agreement(self.teacher, [world()])
        self.assertEqual(check.status, "warn")
        self.assertEqual(check.issues[0].code, "official.uncovered")
        self.assertEqual(official_agreement(self.teacher, [world(block_x=1.)]).status, "fail")
        positive = world(block_x=1.)
        positive.official["success"][:] = True
        self.assertEqual(official_agreement(self.teacher, [positive]).status, "warn")

    def test_official_tolerance_and_constant_disagreement(self):
        states = world(200, block_x=[0.2] * 199 + [1.])
        states.official["success"][[0, 199]] = True
        self.assertEqual(official_agreement(self.teacher, [states]).status, "pass")
        states.official["success"][1] = True
        self.assertEqual(official_agreement(self.teacher, [states]).status, "fail")
        states.official["success"][:] = False
        self.assertEqual(official_agreement(self.teacher, [states]).status, "fail")

    def test_missing_official_and_example_limit(self):
        state = world()
        state.official.clear()
        check = official_agreement(self.teacher, [state, world()])
        self.assertEqual(check.status, "fail")
        self.assertEqual(check.issues[0].code, "official.missing")
        check = official_agreement(self.teacher, [world(10, block_x=1.)])
        self.assertEqual(len(check.stats["entries"][0]["mismatches"]), 5)

    def test_run_stats_and_seed_reset(self):
        good = successful_trajectory().states
        frames = [good.index(torch.tensor([i])) for i in range(good.N)]
        check, states, cached = _run_frames(self.teacher, [frames, frames])
        self.assertEqual(check.status, "pass")
        self.assertEqual(check.stats["num_states"], 12)
        self.assertEqual(check.stats["num_regressions"], 0)
        self.assertAlmostEqual(check.stats["stage_occupancy"]["done"], 1 / 6)
        self.assertAlmostEqual(check.stats["guidance_fraction"], 5 / 6)
        self.assertAlmostEqual(check.stats["instance_fraction_true"]["grasped(g, block)"], 0.5)
        self.assertEqual(official_agreement(self.teacher, states, evaluations=cached).status, "pass")

    def test_run_reports_invalid_predicate_and_progress(self):
        for result in (torch.tensor([float("inf")]), torch.zeros(1, 1)):
            predicates = {**self.candidate.predicates, "near": lambda *a, **kw: result}
            check, _, _ = _run_frames(Teacher(replace(self.candidate, predicates=predicates), 1), [[world()]])
            self.assertEqual(check.status, "fail")
            self.assertIn("near(g, block)", check.issues[0].message)
            self.assertIn("Traceback", check.issues[0].message)
        candidate = replace(self.candidate, progress={"carry": lambda *a, **kw: torch.tensor([float("nan")])})
        check, _, _ = _run_frames(Teacher(candidate, 1), [[world()]])
        self.assertEqual(check.status, "fail")
        self.assertIn("progress_carry", check.issues[0].message)

    def test_trajectory_coverage_and_pass_through(self):
        good = successful_trajectory()
        check, summary = trajectory_checks(self.teacher, [good])
        self.assertEqual(check.status, "pass")
        self.assertTrue(summary["trajectories"][0]["done"])
        stuck = Trajectory(WorldState.cat([world(), world()]), True, "stuck")
        check, _ = trajectory_checks(self.teacher, [stuck])
        self.assertIn("trajectory.constant_literal", [i.code for i in check.issues])
        self.assertIn("trajectory.pass_through", [i.code for i in check.issues])
        self.assertEqual(trajectory_checks(self.teacher, [good] * 9 + [stuck])[0].status, "pass")
        self.assertEqual(trajectory_checks(self.teacher, [good] * 8 + [stuck] * 2)[0].status, "fail")
        # Unsuccessful data is summarized but cannot supply coverage or enter the ratio.
        self.assertEqual(trajectory_checks(self.teacher, [replace(good, success=False), stuck])[0].status, "fail")
        self.assertEqual(trajectory_checks(self.teacher, [good, replace(stuck, success=False)])[0].status, "pass")
        self.assertEqual(trajectory_checks(self.teacher, [])[0].status, "fail")

    def test_regression_disqualifies_a_trajectory_that_reaches_done(self):
        good = successful_trajectory()
        state = WorldState.cat([good.states, world(), world()])
        check, summary = trajectory_checks(self.teacher, [Trajectory(state, True, "regressed")])
        self.assertEqual(check.stats["pass_through_ratio"], 0.0)
        self.assertTrue(summary["trajectories"][0]["reached_done"])
        self.assertTrue(summary["trajectories"][0]["regressions"])

    def test_reports_round_trip_and_status(self):
        check = CheckResult("official", "warn", [Issue("official.uncovered", "constant", "success")], {"n": 2})
        report = Layer1Report(TOY, "toy", False, [check], {"trajectories": []}, "start", "end")
        self.assertTrue(report.passed)
        restored = Layer1Report.from_json(report.to_json())
        self.assertEqual(restored, report)
        self.assertIn("official.uncovered", restored.to_markdown())
        self.assertIn("Replay summary", restored.to_markdown())
        self.assertIn("Result: PASS", restored.to_markdown())
        self.assertFalse(Layer1Report(TOY, "toy", True, [CheckResult("run", "fail")], None, "", "").passed)

    def test_parse_schema_and_ast_gate_without_simulator(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "candidate"
            shutil.copytree(TOY, path)
            (path / "predicates.py").write_text("def broken(:\n")
            (path / "stage_graph.yaml").write_text("stages: [\n")
            report = validate_layer1(path, "unused", isolate=False)
            self.assertEqual(len(report.checks[0].issues), 2)
            self.assertTrue(all(c.status == "skipped" for c in report.checks[1:]))
            shutil.copytree(TOY, path, dirs_exist_ok=True)
            graph = (path / "stage_graph.yaml").read_text().replace("regress_to: grasp", "regress_to: absent")
            graph = graph.replace('"in_region(block, region)"', '"missing(block, absent)"')
            (path / "stage_graph.yaml").write_text(graph)
            report = validate_layer1(path, "unused", isolate=False)
            self.assertEqual(report.checks[1].status, "fail")
            self.assertGreater(len(report.checks[1].issues), 2)
            shutil.copytree(TOY, path, dirs_exist_ok=True)
            pred = path / "predicates.py"
            pred.write_text(pred.read_text().replace("return g.width - min_width", "return g.name"))
            report = validate_layer1(path, "unused")
            self.assertEqual([c.status for c in report.checks], ["pass", "pass", "fail", "skipped", "skipped", "skipped"])

    def test_extra_states_are_only_used_for_official(self):
        class Env:
            def __init__(self):
                self.action_space = self

            def reset(self, **kwargs): pass
            def seed(self, seed): pass
            def close(self): pass

        class Adapter:
            device = "cpu"

            def __init__(self, *args): pass
            def snapshot(self): return world()

        positive = world(block_x=1.)
        positive.official["success"][:] = True
        with patch("vpmkit.adapters.maniskill.make_env", return_value=Env()), patch("vpmkit.adapters.maniskill.ManiSkillAdapter", Adapter):
            report = validate_layer1(TOY, "mock", num_envs=1, seeds=(0,), steps=0,
                                     extra_states=[positive], isolate=False)
        self.assertTrue(report.passed, report.to_markdown())
        self.assertEqual(report.checks[3].stats["num_states"], 1)
        self.assertEqual(report.checks[4].status, "pass")
        self.assertEqual(report.checks[4].stats["entries"][0]["num_states"], 2)
        self.assertEqual(report.checks[5].status, "skipped")
        self.assertIsNone(report.replay_summary)


if __name__ == "__main__":
    unittest.main()
