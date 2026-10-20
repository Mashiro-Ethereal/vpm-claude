"""Opt-in simulator validation; every GPU environment is created in its own child."""

from copy import deepcopy
import os
from pathlib import Path
import tempfile
import textwrap
import unittest

import torch

from vpmkit.adapters import ManiSkillAdapter, make_env
from vpmkit.artifact.loader import load_candidate
from vpmkit.validate.layer1 import validate_layer1
from vpmkit.validate.replay import record_rollout, replay_env_states
from vpmkit.world import WorldState


GRAPH = """
task: Pick up the cube and hold it at the goal with a static arm
objects:
  g: {name: gripper}
  cube: {name: cube}
  goal: {name: goal}
stages:
  - name: reach
    exit: ["gripper_open(g)", "near(g, cube)"]
  - name: grasp
    exit: ["grasped(g, cube)"]
  - name: carry
    exit: ["at_goal(cube, goal)"]
    invariants:
      - literal: grasped(g, cube)
        regress_to: grasp
        event: "Regrasp {cube} with {g}."
  - name: settle
    exit: ["at_goal(cube, goal)", "arm_static(g)"]
official:
  - {literals: ["grasped(g, cube)"], key: is_grasped}
  - {literals: ["at_goal(cube, goal)"], key: is_obj_placed}
  - {literals: ["arm_static(g)"], key: is_robot_static}
  - {literals: ["at_goal(cube, goal)", "arm_static(g)"], key: success}
"""

PREDICATES = """
import torch
from vpmkit.api import G, predicate

@predicate(desc="Gripper is open", need_true="Open {g}.", need_false="Close {g}.", scale=0.08)
def gripper_open(w, g, *, min_width=0.04):
    return g.width - min_width

@predicate(desc="Gripper is near the cube", need_true="Move {g} near {cube}.", scale=0.2)
def near(w, g, cube, *, max_dist=0.1):
    return max_dist - G.dist(g.pos, cube.pos)

@predicate(desc="Gripper grasps the cube", need_true="Grasp {cube} with {g}.")
def grasped(w, g, cube):
    return w.grasping(g, cube)

@predicate(desc="Cube is within the goal radius", need_true="Move {cube} to {goal}.", scale=0.1)
def at_goal(w, cube, goal, *, radius=0.025):
    return radius - torch.linalg.norm(goal.pos - cube.pos, axis=1)

@predicate(desc="Arm joint speeds are at most the static threshold", need_true="Hold {g} still.")
def arm_static(w, g, *, threshold=0.2):
    return threshold - torch.max(torch.abs(g.arm_qvel), 1)[0]
"""

BINDINGS = """
def bind(env, api):
    return {
        "g": api.gripper(),
        "cube": api.actor(env.cube, [env.cube_half_size] * 3),
        "goal": api.site(lambda: env.goal_site.pose),
    }
"""


def write_candidate(path, predicates=PREDICATES):
    path.mkdir()
    for name, text in (("stage_graph.yaml", GRAPH), ("predicates.py", predicates), ("bindings.py", BINDINGS)):
        (path / name).write_text(textwrap.dedent(text))
    return path


@unittest.skipUnless(os.environ.get("VPM_RUN_MANISKILL") == "1", "set VPM_RUN_MANISKILL=1")
class ValidateManiSkillTests(unittest.TestCase):
    def test_valid_candidate_default_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = write_candidate(Path(temp) / "candidate")
            report = validate_layer1(candidate, "PickCube-v1")
        self.assertTrue(report.passed, report.to_markdown())
        self.assertEqual(report.checks[3].status, "pass")
        self.assertEqual(report.checks[3].stats["num_states"], 8 * 3 * 31)
        self.assertIn(report.checks[4].status, ("pass", "warn"))

    def test_official_threshold_with_covering_states(self):
        from mani_skill.utils.structs.pose import Pose

        with tempfile.TemporaryDirectory() as temp:
            candidate = write_candidate(Path(temp) / "candidate")
            env = make_env("PickCube-v1", num_envs=1, seed=0)
            try:
                base = env.unwrapped
                adapter = ManiSkillAdapter(env, load_candidate(candidate).bind)
                base.cube.set_pose(Pose.create_from_pq(base.goal_site.pose.p.clone()))
                at_goal = adapter.snapshot()
                self.assertTrue(at_goal.official["is_obj_placed"][0])
                shifted = base.goal_site.pose.p.clone()
                shifted[:, 0] += 0.1
                base.cube.set_pose(Pose.create_from_pq(shifted))
                near_goal = adapter.snapshot()
                self.assertFalse(near_goal.official["is_obj_placed"][0])
            finally:
                env.close()
            extra = [at_goal, near_goal]
            report = validate_layer1(candidate, "PickCube-v1", seeds=(0,), steps=0, extra_states=extra)
            self.assertTrue(report.passed, report.to_markdown())
            entry = next(e for e in report.checks[4].stats["entries"] if e["key"] == "is_obj_placed")
            self.assertEqual(entry["status"], "pass")
            broken = write_candidate(Path(temp) / "broken", PREDICATES.replace("radius=0.025", "radius=0.25"))
            report = validate_layer1(broken, "PickCube-v1", seeds=(0,), steps=0, extra_states=extra)
            self.assertEqual(report.checks[4].status, "fail", report.to_markdown())
            self.assertFalse(report.passed)

    def test_forbidden_attribute(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = write_candidate(Path(temp) / "candidate", PREDICATES.replace("return g.width - min_width", "return g.name"))
            report = validate_layer1(candidate, "PickCube-v1")
        self.assertEqual(report.checks[2].status, "fail", report.to_markdown())
        self.assertEqual(report.checks[3].status, "skipped")

    def test_nonfinite_predicate(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = write_candidate(Path(temp) / "candidate", PREDICATES.replace("return g.width - min_width", "return g.width / 0"))
            report = validate_layer1(candidate, "PickCube-v1", seeds=(0,), steps=1)
        self.assertEqual(report.checks[3].status, "fail", report.to_markdown())
        self.assertIn("gripper_open(g)", report.checks[3].issues[0].message)

    def test_replay_env_states_and_record_rollout(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = write_candidate(Path(temp) / "candidate")
            env = make_env("PickCube-v1", num_envs=1, seed=5)
            try:
                adapter = ManiSkillAdapter(env, load_candidate(candidate).bind)
                env.action_space.seed(5)
                states, snapshots = [], []
                for frame in range(11):
                    if frame:
                        env.step(env.action_space.sample())
                    states.append(deepcopy(env.unwrapped.get_state_dict()))
                    snapshots.append(adapter.snapshot())
                actual = replay_env_states(env, adapter, states)
                expected = WorldState.cat(snapshots)
                self.assertEqual(actual.N, 11)
                for handle, obj in expected.objects.items():
                    for field in ("pos", "quat", "linvel", "angvel", "half_size"):
                        # PhysX reconstructs link velocities from articulation state;
                        # this rollout differs by < 0.001 m/s (or rad/s) after restore.
                        atol = 1e-3 if obj.kind == "gripper" and field in {"linvel", "angvel"} else 1e-5
                        with self.subTest(handle=handle, field=field):
                            torch.testing.assert_close(getattr(actual.objects[handle], field), getattr(obj, field), atol=atol, rtol=1e-5)
                    for key, value in obj.attrs.items():
                        torch.testing.assert_close(actual.objects[handle].attrs[key], value, atol=1e-5, rtol=1e-5)
                for field in ("official", "grasping", "contacts"):
                    for key, value in getattr(expected, field).items():
                        torch.testing.assert_close(getattr(actual, field)[key], value, atol=1e-5, rtol=1e-5)
                rollout = record_rollout(env, adapter, lambda obs: env.action_space.sample(), 10, 5)
                self.assertEqual(rollout.states.N, 11)
                self.assertEqual(rollout.success, bool(env.unwrapped.evaluate()["success"][0]))
                torch.testing.assert_close(rollout.states.objects["cube"].pos, expected.objects["cube"].pos)
            finally:
                env.close()


if __name__ == "__main__":
    unittest.main()
