"""Batched potential-based shaping before ManiSkill vector auto-reset."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import gymnasium as gym
import torch
from torch import Tensor

from ..candidate import Candidate
from ..teacher import Teacher

if TYPE_CHECKING:
    from ..adapters.maniskill import ManiSkillAdapter


class PBRSWrapper(gym.Wrapper):
    """Wrap inside ManiSkillVectorEnv with the learner's discount factor.

    Adapter and teacher instances can be injected for simulation-free tests.
    """

    def __init__(self, env: gym.Env, candidate: Candidate, gamma: float,
                 r_bonus: float, params: Mapping[str, float] | None = None, *,
                 adapter: ManiSkillAdapter | None = None,
                 teacher: Teacher | None = None) -> None:
        super().__init__(env)
        self.num_envs = env.unwrapped.num_envs
        self.device = env.unwrapped.device
        self.gamma = gamma
        self.r_bonus = r_bonus
        if adapter is None:
            from ..adapters.maniskill import ManiSkillAdapter

            adapter = ManiSkillAdapter(env, candidate.bind)
        self.adapter = adapter
        self.teacher = (Teacher(candidate, self.num_envs, self.device, params)
                        if teacher is None else teacher)
        self.phi_prev = torch.empty(self.num_envs, dtype=torch.float32, device=self.device)

    def reset(self, *, seed: int | list[int] | None = None,
              options: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
        obs, info = self.env.reset(seed=seed, options=options)
        env_mask = None
        if options is not None and "env_idx" in options:
            env_idx = options["env_idx"]
            self.teacher.reset(env_idx=env_idx)
            env_mask = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
            env_mask[env_idx] = True
        else:
            self.teacher.reset()
        out = self.teacher.step(self.adapter.snapshot(info), env_mask=env_mask)
        self.phi_prev = (out["phi"] if env_mask is None
                         else torch.where(env_mask, out["phi"], self.phi_prev))
        return obs, info

    def step(self, action: Any) -> tuple[Any, Tensor, Tensor, Tensor, dict[str, Any]]:
        obs, _, terminated, truncated, info = self.env.step(action)
        out = self.teacher.step(self.adapter.snapshot(info))
        phi_next = out["phi"]
        phi_prev = self.phi_prev
        phi_used = torch.where(terminated, 0.0, phi_next)
        shaping = self.gamma * phi_used - phi_prev
        reward = (shaping + info["success"] * self.r_bonus).to(torch.float32)
        self.phi_prev = phi_next
        info["pbrs"] = {"phi": phi_next, "phi_prev": phi_prev, "phi_used": phi_used,
                        "stage": out["stage"], "shaping": shaping,
                        "elapsed_steps": info["elapsed_steps"].clone()}
        return obs, reward, terminated, truncated, info
