"""SAC final-observation bootstrap and repeated evaluation without simulation."""

import unittest

import torch

from scripts.sac_check import evaluate_resets, replay_transition
from .test_ppo_check import DeterministicAgent, ScriptedVectorEnv


class SACBootstrapTest(unittest.TestCase):
    def test_success_stops_bootstrap_and_truncation_uses_final_observation(self) -> None:
        terminated = torch.tensor([False, True, False, True])
        truncated = torch.tensor([False, False, True, True])
        next_obs = torch.tensor([[11.0], [200.0], [300.0], [400.0]])
        final_obs = torch.tensor([[11.0], [22.0], [33.0], [44.0]])
        real_next_obs, stop = replay_transition(
            next_obs, terminated, truncated, {"final_observation": final_obs})
        torch.testing.assert_close(real_next_obs, torch.tensor([[11.0], [200.0], [33.0], [400.0]]))
        self.assertEqual(stop.tolist(), [False, True, False, True])
        rewards = torch.tensor([1.0, 10.0, 2.0, 10.0])
        target = rewards + (~stop).float() * 0.99 * real_next_obs.flatten()
        torch.testing.assert_close(target, torch.tensor([11.89, 10.0, 34.67, 10.0]))
        torch.testing.assert_close(next_obs, torch.tensor([[11.0], [200.0], [300.0], [400.0]]))

    def test_explicit_always_and_never_modes(self) -> None:
        terminated, truncated = torch.tensor([True, False]), torch.tensor([False, True])
        obs, final = torch.tensor([[100.0], [200.0]]), torch.tensor([[1.0], [2.0]])
        real, stop = replay_transition(obs, terminated, truncated, {"final_observation": final}, "always")
        torch.testing.assert_close(real, final)
        self.assertEqual(stop.tolist(), [False, False])
        real, stop = replay_transition(obs, terminated, truncated, {"final_observation": final}, "never")
        torch.testing.assert_close(real, obs)
        self.assertEqual(stop.tolist(), [True, True])


class SACEvaluationTest(unittest.TestCase):
    def test_eight_seeded_resets_aggregate_only_first_episodes(self) -> None:
        env = ScriptedVectorEnv()
        result = evaluate_resets(DeterministicAgent(), env, 10001, 3, ["reach", "grasp", "hold"])
        self.assertEqual(result["seeds"], list(range(10001, 10009)))
        self.assertEqual(env.seed, 10008)
        self.assertEqual(result["episodes"], 24)
        self.assertEqual(len(result["per_environment"]), 24)
        self.assertAlmostEqual(result["success_once"], 2 / 3)
        self.assertEqual(result["length_mean"], 2.0)
        self.assertEqual(result["teacher"], {
            "first_success_stage_histogram": {"reach": 0, "grasp": 8, "hold": 8},
            "first_success_last_stage_fraction": 0.5,
            "unsuccessful_end_stage_histogram": {"reach": 0, "grasp": 8, "hold": 0},
        })
        self.assertEqual([row["seed"] for row in result["per_environment"]],
                         [seed for seed in range(10001, 10009) for _ in range(3)])
