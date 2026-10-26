"""Reward arithmetic and reset bookkeeping without simulation."""

from typing import Any
import unittest

import gymnasium as gym
import torch
from torch import Tensor

from vpmkit.rewards import PBRSWrapper
from .synth import candidate


class ScriptedEnv(gym.Env):
    def __init__(self, resets: list[list[float]], steps: list[dict[str, Any]]) -> None:
        self.num_envs = len(resets[0])
        self.device = torch.device("cpu")
        self.resets = iter(resets)
        self.steps = iter(steps)
        self.elapsed_steps = torch.zeros(self.num_envs, dtype=torch.long)
        self.observation_space = gym.spaces.Box(-1, 1, (self.num_envs, 1))
        self.action_space = self.observation_space
        self.obs = torch.zeros(self.num_envs, 1)

    def reset(self, *, seed: int | None = None,
              options: dict[str, Any] | None = None) -> tuple[Tensor, dict[str, Tensor]]:
        self.reset_args = (seed, options)
        indices = options["env_idx"] if options is not None and "env_idx" in options else slice(None)
        self.elapsed_steps[indices] = 0
        self.info = {"scripted_phi": torch.tensor(next(self.resets)),
                     "elapsed_steps": self.elapsed_steps}
        return self.obs, self.info

    def step(self, action: Tensor) -> tuple[Tensor, Tensor, Tensor, Tensor, dict[str, Tensor]]:
        self.action = action
        frame = next(self.steps)
        self.elapsed_steps += 1
        self.info = {"scripted_phi": torch.tensor(frame["phi"]),
                     "success": torch.tensor(frame["success"]), "elapsed_steps": self.elapsed_steps}
        return (self.obs, torch.full((self.num_envs,), 999.0), torch.tensor(frame["terminated"]),
                torch.tensor(frame["truncated"]), self.info)


class FakeAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def snapshot(self, info: dict[str, Tensor]) -> Tensor:
        self.calls += 1
        return info["scripted_phi"]


class FakeTeacher:
    def __init__(self) -> None:
        self.resets: list[Tensor | None] = []
        self.masks: list[Tensor | None] = []

    def reset(self, env_idx: Tensor | None = None) -> None:
        self.resets.append(env_idx)

    def step(self, snapshot: Tensor, env_mask: Tensor | None = None) -> dict[str, Tensor]:
        self.masks.append(env_mask)
        return {"phi": snapshot.clone(), "stage": torch.zeros_like(snapshot, dtype=torch.long)}


class PBRSTest(unittest.TestCase):
    def test_scaled_shaping_and_discounted_telescope(self) -> None:
        frames = [
            {"phi": [0.5, 0.4], "success": [False, False],
             "terminated": [False, False], "truncated": [False, False]},
            {"phi": [0.7, 0.2], "success": [False, False],
             "terminated": [False, False], "truncated": [False, False]},
            {"phi": [0.9, 0.8], "success": [True, False],
             "terminated": [True, False], "truncated": [False, True]},
        ]
        gamma, bonus = 0.99, 10.0
        with candidate() as c:
            wrappers = [PBRSWrapper(ScriptedEnv([[0.3, 0.6]], frames), c, gamma, bonus,
                                    phi_scale=scale, adapter=FakeAdapter(), teacher=FakeTeacher())
                        for scale in (1.0, 4.0)]
        for wrapper in wrappers:
            wrapper.reset()
        initial = wrappers[1].phi_prev.clone()
        discounted = torch.zeros(2)
        for step in range(len(frames)):
            results = [wrapper.step(torch.zeros(2, 1)) for wrapper in wrappers]
            base, scaled = [result[-1]["pbrs"] for result in results]
            for key in ("phi", "phi_prev", "phi_used", "shaping"):
                torch.testing.assert_close(scaled[key], 4 * base[key], rtol=0, atol=0)
            torch.testing.assert_close(scaled["phi_teacher"], base["phi_teacher"], rtol=0, atol=0)
            torch.testing.assert_close(scaled["phi"], 4 * scaled["phi_teacher"], rtol=0, atol=0)
            for _, reward, _, _, info in results:
                torch.testing.assert_close(reward, info["pbrs"]["shaping"] + info["success"] * bonus)
            discounted += gamma ** step * scaled["shaping"]
        torch.testing.assert_close(scaled["phi_used"], torch.tensor([0.0, 3.2]))
        torch.testing.assert_close(discounted, gamma ** len(frames) * scaled["phi_used"] - initial,
                                   rtol=0, atol=1e-6)

    def test_success_and_truncation_telescope_with_bonus(self) -> None:
        env = ScriptedEnv([[0.3, 0.6]], [
            {"phi": [0.5, 0.4], "success": [False, False],
             "terminated": [False, False], "truncated": [False, False]},
            {"phi": [0.7, 0.2], "success": [False, False],
             "terminated": [False, False], "truncated": [False, False]},
            {"phi": [0.9, 0.8], "success": [True, False],
             "terminated": [True, False], "truncated": [False, True]},
        ])
        adapter, teacher = FakeAdapter(), FakeTeacher()
        gamma, bonus = 0.8, 2.5
        with candidate() as c:
            wrapper = PBRSWrapper(env, c, gamma, bonus, adapter=adapter, teacher=teacher)
        obs, info = wrapper.reset(seed=17)
        self.assertIs(obs, env.obs)
        self.assertIs(info, env.info)
        self.assertEqual(env.reset_args, (17, None))
        initial = wrapper.phi_prev.clone()
        discounted = torch.zeros(2)
        previous = initial
        action = torch.zeros(2, 1)
        for t in range(3):
            obs, reward, terminated, truncated, info = wrapper.step(action)
            self.assertIs(obs, env.obs)
            self.assertIs(info, env.info)
            self.assertIs(env.action, action)
            self.assertEqual((reward.dtype, reward.shape, reward.device), (torch.float32, (2,), env.device))
            pbrs = info["pbrs"]
            torch.testing.assert_close(pbrs["phi_prev"], previous, rtol=0, atol=0)
            torch.testing.assert_close(reward - pbrs["shaping"],
                                       torch.tensor([bonus if t == 2 else 0.0, 0.0]))
            torch.testing.assert_close(reward, gamma * pbrs["phi_used"] - previous + info["success"] * bonus)
            discounted += gamma ** t * pbrs["shaping"]
            previous = pbrs["phi"].clone()
        self.assertEqual(terminated.tolist(), [True, False])
        self.assertEqual(truncated.tolist(), [False, True])
        torch.testing.assert_close(pbrs["phi_used"], torch.tensor([0.0, 0.8]))
        torch.testing.assert_close(discounted, torch.tensor([-0.3, gamma ** 3 * 0.8 - 0.6]), atol=1e-6, rtol=0)
        torch.testing.assert_close(wrapper.phi_prev, torch.tensor([0.9, 0.8]))
        self.assertEqual(adapter.calls, 4)
        self.assertEqual(len(teacher.masks), 4)

    def test_partial_reset_refreshes_only_selected_potentials(self) -> None:
        env = ScriptedEnv([[0.1, 0.2], [0.4, 9.0]], [
            {"phi": [0.8, 0.6], "success": [False, False],
             "terminated": [False, False], "truncated": [True, False]},
            {"phi": [0.5, 0.7], "success": [False, False],
             "terminated": [False, False], "truncated": [False, False]},
        ])
        adapter, teacher = FakeAdapter(), FakeTeacher()
        with candidate() as c:
            wrapper = PBRSWrapper(env, c, 0.8, 1.0, adapter=adapter, teacher=teacher)
        wrapper.reset()
        _, _, _, _, info = wrapper.step(torch.zeros(2, 1))
        saved = {key: value.clone() for key, value in info["pbrs"].items()}
        indices = torch.tensor([0])
        options = {"env_idx": indices}
        obs, reset_info = wrapper.reset(options=options)
        self.assertIs(obs, env.obs)
        self.assertIs(reset_info, env.info)
        self.assertEqual(set(reset_info), {"scripted_phi", "elapsed_steps"})
        self.assertIs(env.reset_args[1], options)
        self.assertIsNone(teacher.resets[0])
        self.assertIs(teacher.resets[1], indices)
        self.assertEqual(teacher.masks[-1].tolist(), [True, False])
        torch.testing.assert_close(wrapper.phi_prev, torch.tensor([0.4, 0.6]))
        _, _, _, _, next_info = wrapper.step(torch.zeros(2, 1))
        torch.testing.assert_close(next_info["pbrs"]["phi_prev"], torch.tensor([0.4, 0.6]))
        for key, value in saved.items():
            torch.testing.assert_close(info["pbrs"][key], value, rtol=0, atol=0)
        self.assertEqual(adapter.calls, 4)
        self.assertEqual(len(teacher.masks), 4)
