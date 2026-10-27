"""Observer bookkeeping and trajectory statistics without simulation."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gymnasium as gym
import numpy as np
import torch

from scripts.teacher_check import (
    TeacherObserver, candidate_statistics, compare_candidates, concatenate_rollouts,
    episode_classes, official_correspondence, rollout, sanity_check, spearman,
)
from vpmkit.automaton import Automaton
from vpmkit.candidate.schema import StageGraph

INSTANCES = ["near(g, cube)", "grasped(g, cube)", "at_goal(cube, goal)", "arm_static(g)"]


def graph() -> StageGraph:
    return StageGraph.model_validate({
        "task": "Move the cube to the goal.",
        "objects": {name: {"name": name} for name in ("g", "cube", "goal")},
        "stages": [
            {"name": "reach", "exit": [INSTANCES[0]]},
            {"name": "grasp", "exit": [INSTANCES[1]],
             "invariants": [{"literal": INSTANCES[0], "regress_to": "reach"}]},
            {"name": "carry", "exit": [INSTANCES[2]],
             "invariants": [{"literal": INSTANCES[1], "regress_to": "reach"}]},
            {"name": "hold", "exit": [INSTANCES[3]],
             "invariants": [{"literal": INSTANCES[2], "regress_to": "carry"}]},
        ],
        "official": [{"key": "is_grasped", "literals": [INSTANCES[1]]},
                     {"key": "success", "literals": INSTANCES[2:]}],
    })


def sequence(stages=None, phi=None, *, length=None, success=True, initial_distance=0.2) -> dict:
    stages = [0, 1, 1, 2, 3] if stages is None else stages
    phi = [0.1, 0.25, 0.25, 0.6, 1.0] if phi is None else phi
    stage, potential = torch.tensor([stages], dtype=torch.int8), torch.tensor([phi])
    count = len(stages)
    length = count - 1 if length is None else length
    mask = torch.arange(count)[None, :] <= length
    official_mask = mask.clone()
    official_mask[:, 0] = False
    pred = torch.stack((stage >= 1, stage >= 2, stage >= 3, stage >= 3), -1)
    output = {"stage": stage, "phi": potential, "stage_progress": 4 * potential - stage,
              "pred": pred, "margin": torch.where(pred, 1.0, -1.0),
              "guidance": ~pred}
    official = {"success": torch.zeros_like(mask), "is_grasped": pred[..., 1].clone(),
                "is_obj_placed": pred[..., 2].clone(), "is_robot_static": pred[..., 3].clone()}
    official["success"][0, length] = success
    return {"teachers": {"generated": output,
                         "reference": {key: value.clone() for key, value in output.items()}},
            "geom": {"cube_goal_dist": torch.full((1, count), initial_distance),
                     "tcp_cube_dist": torch.tensor([[0.1 / (t + 1) for t in range(count)]]),
                     "cube_z": torch.zeros(1, count)},
            "official": official, "mask": mask, "official_mask": official_mask,
            "lengths": torch.tensor([length], dtype=torch.uint8),
            "seed": torch.tensor([10001], dtype=torch.int32), "env_index": torch.tensor([0]),
            "terminated": torch.tensor([success]), "truncated": torch.tensor([not success])}


def statistics(data: dict) -> dict:
    return candidate_statistics(data, "generated", graph(), INSTANCES)


class StatisticsTest(unittest.TestCase):
    def test_clean_chain_timing_geometry_and_phi(self) -> None:
        result = statistics(sequence())
        self.assertEqual(result["a_chain"]["chain_coverage"], 1.0)
        self.assertEqual(result["a_chain"]["success_stage_histogram"]["hold"], 1)
        self.assertEqual(result["b_regressions"]["total"], 0)
        timing = result["c_timing"]["stages"]
        self.assertEqual([timing[name]["first_entry"]["mean"] for name in timing], [0, 1, 3, 4])
        self.assertEqual([timing[name]["dwell"]["mean"] for name in timing], [1, 2, 1, 1])
        self.assertAlmostEqual(result["c_timing"]["entry_geometry_m"]["tcp_cube_at_grasp_entry"]["mean"], 0.05)
        self.assertAlmostEqual(result["c_timing"]["entry_geometry_m"]["tcp_cube_at_first_grasped"]["mean"], 0.025)
        dynamics = result["d_phi"]
        self.assertEqual(dynamics["plateau_step_fraction"], 0.25)
        self.assertEqual(dynamics["plateau_by_destination_stage"]["grasp"]["fraction"], 0.5)
        self.assertEqual(dynamics["no_negative_step_episode_fraction"], 1.0)
        self.assertEqual(dynamics["forward_transitions"]["grasp -> carry"]["count"], 1)
        self.assertTrue(result["phi_identity"]["exact"])

    def test_regression_readvances_past_declared_target(self) -> None:
        automaton = Automaton([[0], [1], [2], [3]], [(1, 0, 0), (2, 1, 0), (3, 2, 2)], 4)
        target, _ = automaton.step(torch.tensor([2]), torch.zeros(1, 3, dtype=torch.long),
                                   torch.tensor([[True, False, False, False]]))
        self.assertEqual(target.item(), 1)
        data = sequence([0, 1, 2, 1, 2, 3], [0.1, 0.25, 0.6, 0.25, 0.6, 1.0])
        result = statistics(data)
        pair = result["b_regressions"]["pairs"]["carry -> grasp"]
        self.assertEqual(pair, {"count": 1, "invariants": [
            {"literal": INSTANCES[1], "regress_to": "reach", "false_count": 1}],
            "no_false_invariant_count": 0})
        self.assertEqual(result["a_chain"]["completed_fraction"], 1.0)
        self.assertEqual(result["a_chain"]["chain_coverage"], 0.0)
        self.assertEqual(result["b_regressions"]["episodes_with_regression"]["non_trivial_success"], 1)
        self.assertAlmostEqual(result["d_phi"]["largest_single_drop"], 0.35)
        self.assertAlmostEqual(result["d_phi"]["negative_mass_per_episode"]["mean"], 0.35)
        self.assertEqual(result["d_phi"]["stage_decrease_fraction"], 0.2)

    def test_multistage_jump_counts_skipped_stage_and_forward_pair(self) -> None:
        result = statistics(sequence([0, 2, 3], [0.1, 0.6, 1.0]))
        timing = result["c_timing"]["stages"]
        self.assertEqual(timing["grasp"]["first_entry"]["mean"], 1)
        self.assertEqual(timing["grasp"]["dwell"]["mean"], 0)
        self.assertEqual(timing["grasp"]["skipped_fraction"], 1)
        self.assertEqual(result["d_phi"]["forward_transitions"]["reach -> carry"]["count"], 1)
        self.assertEqual(result["a_chain"]["chain_coverage"], 1)

    def test_trivial_success_uses_initial_distance_and_is_excluded(self) -> None:
        data = sequence([0, 0], [0.1, 0.1], initial_distance=0.025)
        classes = episode_classes(data, 0.025)
        self.assertTrue(classes["trivial_success"].item())
        self.assertFalse(classes["non_trivial_success"].item())
        self.assertEqual(statistics(data)["a_chain"]["episodes"], 0)
        self.assertIsNone(statistics(data)["a_chain"]["chain_coverage"])
        data["geom"]["cube_goal_dist"][:, 0] = 0.026
        self.assertTrue(episode_classes(data, 0.025)["non_trivial_success"].item())

    def test_mask_excludes_post_episode_regression_success_and_mismatch(self) -> None:
        data = sequence([0, 1, 2, 0, 3], [0.1, 0.25, 0.6, -99.0, 1.0], length=2, success=False)
        data["official"]["success"][0, 4] = True
        data["official"]["is_grasped"][0, 3] = True
        result = statistics(data)
        self.assertTrue(episode_classes(data, 0.025)["failure"].item())
        self.assertEqual(result["b_regressions"]["total"], 0)
        self.assertEqual(result["f_failures"]["last_stage_histogram"]["carry"], 1)
        self.assertEqual(result["e_official"]["is_grasped"]["mismatch_count"], 0)
        self.assertTrue(result["phi_identity"]["exact"])
        self.assertEqual(result["phi_identity"]["steps"], 3)
        data["teachers"]["reference"]["phi"][0, 4] = 100
        self.assertEqual(compare_candidates(data, [s.name for s in graph().stages])["abs_phi_difference"]["max"], 0)

    def test_official_conjunction_and_mismatch_margin(self) -> None:
        data = sequence()
        output = data["teachers"]["generated"]
        output["pred"][0, 3, 2:] = torch.tensor([True, False])
        self.assertEqual(official_correspondence(data, output, graph(), INSTANCES)["success"]["mismatch_count"], 0)
        data["official"]["success"][0, 3] = True
        output["margin"][0, 3, 3] = -0.5
        result = official_correspondence(data, output, graph(), INSTANCES)["success"]
        self.assertEqual(result["agreement_rate"], 0.75)
        self.assertEqual(result["examples"][0]["t"], 3)
        self.assertEqual(result["examples"][0]["margins"][INSTANCES[3]], -0.5)

    def test_official_negation(self) -> None:
        data = sequence()
        spec = graph().model_copy(update={"official": []})
        spec = StageGraph.model_validate({**spec.model_dump(), "official": [
            {"key": "not_grasped", "literals": ["not grasped(g, cube)"]}]})
        data["official"]["not_grasped"] = ~data["official"]["is_grasped"]
        result = official_correspondence(data, data["teachers"]["generated"], spec, INSTANCES)
        self.assertEqual(result["not_grasped"]["agreement_rate"], 1)

    def test_same_stage_phi_drop_and_identity_violation(self) -> None:
        data = sequence([0, 0, 2, 3], [0.2, 0.1, 0.6, 1.0])
        result = statistics(data)
        self.assertAlmostEqual(result["d_phi"]["same_stage_decrease_fraction"], 1 / 3)
        self.assertEqual(result["d_phi"]["negative_by_destination_stage"]["reach"]["fraction"], 1)
        data["teachers"]["generated"]["stage_progress"][0, 1] += 0.1
        self.assertEqual(statistics(data)["phi_identity"]["mismatch_count"], 1)

    def test_comparison_grouping_and_concatenation(self) -> None:
        data = concatenate_rollouts([sequence(), sequence()])
        data["teachers"]["reference"]["phi"][:, 3] -= 0.1
        result = compare_candidates(data, [s.name for s in graph().stages])
        self.assertEqual(result["steps"], 10)
        self.assertEqual(result["equal_stage_fraction"], 1)
        self.assertAlmostEqual(result["abs_phi_difference"]["mean"], 0.02)
        self.assertAlmostEqual(result["by_generated_stage"]["carry"]["mean"], 0.1)
        result = sanity_check(data, {"episodes": 2, "success_once": 1.0, "length_mean": 4.0})
        self.assertTrue(result["all_exact"])

    def test_spearman_average_ties_reverse_and_constant(self) -> None:
        time = torch.arange(4)
        self.assertAlmostEqual(spearman(time, time), 1)
        self.assertAlmostEqual(spearman(time, -time), -1)
        self.assertAlmostEqual(spearman(torch.tensor([1, 2, 2, 4]), time), np.sqrt(0.9))
        self.assertIsNone(spearman(torch.ones(4), time))
        self.assertIsNone(spearman(torch.ones(1), torch.ones(1)))


class FakeVectorEnv:
    num_envs = 2
    device = torch.device("cpu")
    single_action_space = SimpleNamespace(low=np.array([-1.0]), high=np.array([1.0]))

    def frame(self, t: int) -> dict:
        out = {key: value[:, t].expand(2, *value.shape[2:]).clone()
               for key, value in sequence()["teachers"]["generated"].items()}
        return {"teacher_check": {"generated": out, "reference": out,
                                  "geom": {key: torch.full((2,), 0.2) for key in
                                           ("cube_goal_dist", "tcp_cube_dist", "cube_z")}},
                **{key: torch.tensor([t == 1, False]) for key in
                   ("success", "is_grasped", "is_obj_placed", "is_robot_static")}}

    def reset(self, *, seed: int) -> tuple:
        self.seed, self.t = seed, 0
        return torch.zeros(2, 1), self.frame(0)

    def step(self, action: torch.Tensor) -> tuple:
        torch.testing.assert_close(action, torch.ones_like(action))
        self.t += 1
        info = self.frame(0)
        info["final_info"] = self.frame(self.t)
        return (torch.zeros(2, 1), torch.ones(2), torch.tensor([self.t == 1, False]),
                torch.tensor([False, self.t == 3]), info)


class FakeAgent:
    def get_action(self, obs: torch.Tensor, deterministic: bool) -> torch.Tensor:
        assert deterministic
        return torch.full_like(obs, 10.0)


class RolloutTest(unittest.TestCase):
    def test_pre_reset_first_episode_mask_and_action_clipping(self) -> None:
        env = FakeVectorEnv()
        data = rollout(FakeAgent(), env, 10001, True, 3)
        self.assertEqual(data["lengths"].tolist(), [1, 3])
        self.assertEqual(data["mask"].tolist(), [[True, True, False, False], [True] * 4])
        self.assertFalse(data["official_mask"][:, 0].any())
        self.assertEqual(data["teachers"]["generated"]["stage"].tolist(), [[0, 1, 0, 0], [0, 1, 1, 2]])
        self.assertEqual(data["teachers"]["generated"]["stage"].dtype, torch.int8)
        self.assertEqual(episode_classes(data, 0.025)["success"].tolist(), [True, False])


class FakeEnv(gym.Env):
    def __init__(self) -> None:
        self.num_envs, self.device = 2, torch.device("cpu")
        self.observation_space = self.action_space = gym.spaces.Box(-1, 1, (2, 1))
        self.agent = SimpleNamespace(tcp=SimpleNamespace(pose=SimpleNamespace(p=torch.zeros(2, 3))))
        self.cube = SimpleNamespace(pose=SimpleNamespace(p=torch.ones(2, 3)))
        self.goal_site = SimpleNamespace(pose=SimpleNamespace(p=torch.full((2, 3), 2.0)))
        self.reward = torch.tensor([2.0, 3.0])

    def reset(self, *, seed=None, options=None):
        return torch.zeros(2, 1), {}

    def step(self, action):
        self.action = action
        return torch.zeros(2, 1), self.reward, torch.zeros(2, dtype=torch.bool), torch.zeros(2, dtype=torch.bool), {}


class FakeTeacher:
    def __init__(self, candidate, num_envs, device):
        self.stage = torch.zeros(num_envs, dtype=torch.long)

    def reset(self, env_idx=None):
        self.stage[:] = 0 if env_idx is None else self.stage
        if env_idx is not None:
            self.stage[env_idx] = 0

    def step(self, snapshot, env_mask=None):
        self.stage += 1 if env_mask is None else env_mask.long()
        return {"stage": self.stage}


class ObserverTest(unittest.TestCase):
    def test_reward_actions_clones_and_partial_reset(self) -> None:
        env = FakeEnv()
        with patch("vpmkit.adapters.maniskill.ManiSkillAdapter") as adapter, \
                patch("scripts.teacher_check.Teacher", FakeTeacher):
            adapter.return_value.snapshot.return_value = None
            observer = TeacherObserver(env, {"generated": SimpleNamespace(bind=None),
                                             "reference": SimpleNamespace(bind=None)})
        _, reset_info = observer.reset(seed=1)
        self.assertEqual(reset_info["teacher_check"]["generated"]["stage"].tolist(), [1, 1])
        action = torch.ones(2, 1)
        _, reward, _, _, terminal_info = observer.step(action)
        self.assertIs(reward, env.reward)
        self.assertIs(action, env.action)
        self.assertEqual(terminal_info["teacher_check"]["generated"]["stage"].tolist(), [2, 2])
        _, info = observer.reset(options={"env_idx": torch.tensor([0])})
        for label in ("generated", "reference"):
            self.assertEqual(observer.teachers[label].stage.tolist(), [1, 2])
            self.assertEqual(info["teacher_check"][label]["stage"].tolist(), [1, 2])
            self.assertEqual(terminal_info["teacher_check"][label]["stage"].tolist(), [2, 2])
        env.cube.pose.p[:] = 9
        self.assertEqual(terminal_info["teacher_check"]["geom"]["cube_z"].tolist(), [1, 1])
        self.assertAlmostEqual(terminal_info["teacher_check"]["geom"]["cube_goal_dist"][0].item(), np.sqrt(3), places=6)
