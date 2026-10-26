"""PPO bootstrap selection and first-episode evaluation without simulation."""

from types import SimpleNamespace
import unittest

import numpy as np
import torch

from scripts.ppo_check import evaluate
from vpmkit.ppo_bootstrap import final_bootstrap_mask


class BootstrapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.terminated = torch.tensor([False, True, False, True])
        self.truncated = torch.tensor([False, False, True, True])
        self.done = self.terminated | self.truncated
        self.values = torch.tensor([11.0, 22.0, 33.0, 44.0])

    def test_default_bootstraps_only_truncated_not_terminated(self) -> None:
        mask = final_bootstrap_mask(self.done, self.terminated, self.truncated)
        final_values = torch.zeros_like(self.values)
        final_values[mask] = self.values[mask]
        torch.testing.assert_close(final_values, torch.tensor([0.0, 0.0, 33.0, 0.0]))

    def test_flag_bootstraps_every_done_environment(self) -> None:
        mask = final_bootstrap_mask(self.done, self.terminated, self.truncated, True)
        final_values = torch.zeros_like(self.values)
        final_values[mask] = self.values[mask]
        torch.testing.assert_close(final_values, torch.tensor([0.0, 22.0, 33.0, 44.0]))


class ScriptedVectorEnv:
    num_envs = 3
    device = torch.device("cpu")
    single_action_space = SimpleNamespace(low=np.array([-1.0]), high=np.array([1.0]))

    def reset(self, *, seed: int) -> tuple[torch.Tensor, dict]:
        self.seed = seed
        self.steps = iter([
            ([True, False, False], [False, False, False], [2, 1, 0]),
            ([True, False, True], [False, False, False], [0, 1, 1]),
            ([False, False, True], [False, True, False], [0, 1, 2]),
        ])
        return torch.zeros(3, 1), {}

    def step(self, action: torch.Tensor) -> tuple:
        success, truncated, stage = next(self.steps)
        success = torch.tensor(success)
        info = {
            "success": torch.zeros(3, dtype=torch.bool),
            "final_info": {"success": success, "pbrs": {"stage": torch.tensor(stage)}},
        }
        return torch.zeros(3, 1), torch.zeros(3), success, torch.tensor(truncated), info


class DeterministicAgent(torch.nn.Module):
    def get_action(self, obs: torch.Tensor, deterministic: bool = False) -> torch.Tensor:
        assert deterministic
        return torch.zeros_like(obs)


class EvaluationTest(unittest.TestCase):
    def test_pre_reset_stages_and_only_first_episode_are_reported(self) -> None:
        env = ScriptedVectorEnv()
        result = evaluate(DeterministicAgent(), env, 10001, 3, ["reach", "grasp", "hold"])
        self.assertEqual(env.seed, 10001)
        self.assertAlmostEqual(result["success_once"], 2 / 3)
        self.assertAlmostEqual(result["success_at_end"], 2 / 3)
        self.assertEqual(result["length_mean"], 2.0)
        self.assertEqual(result["teacher"], {
            "first_success_stage_histogram": {"reach": 0, "grasp": 1, "hold": 1},
            "first_success_last_stage_fraction": 0.5,
            "unsuccessful_end_stage_histogram": {"reach": 0, "grasp": 1, "hold": 0},
        })
        rows = result["per_environment"]
        self.assertEqual([row["length"] for row in rows], [1, 3, 2])
        self.assertEqual([row["first_success_step"] for row in rows], [1, None, 2])
        self.assertEqual([row["first_success_stage"] for row in rows], ["hold", None, "grasp"])
        self.assertEqual([row["end_stage"] for row in rows], ["hold", "grasp", "grasp"])
