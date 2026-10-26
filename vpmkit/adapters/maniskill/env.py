"""Create ManiSkill environments.

One process may create at most one GPU environment: SAPIEN crashes when a
process creates a second GPU scene. Run every GPU environment in its own
subprocess.
"""

from typing import Any

import gymnasium as gym


def make_env(env_id: str, num_envs: int = 1, **kwargs: Any) -> gym.Env:
    import mani_skill.envs  # Registers the environments.

    options = dict(num_envs=num_envs,
                   sim_backend="physx_cuda" if num_envs > 1 else "physx_cpu",
                   obs_mode="state", reward_mode="sparse", render_mode=None)
    options.update(kwargs)
    return gym.make(env_id, **options)
