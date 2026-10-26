"""Read ManiSkill state into independent tensor snapshots."""

from collections.abc import Callable, Mapping
from itertools import combinations
from types import ModuleType
from typing import Any

import gymnasium as gym
import torch
from torch import Tensor
from mani_skill.utils.structs.pose import Pose

from ...errors import BindingError
from ...world import BodyState, Snapshot
from . import binding as api
from .binding import ActorSpec, BindingSpec, GripperSpec, SiteSpec


class ManiSkillAdapter:
    def __init__(self, env: gym.Env,
                 bind: Callable[[Any, ModuleType], dict[str, BindingSpec]]) -> None:
        self.env = env.unwrapped
        self.device = self.env.device
        self.num_envs = self.env.num_envs
        try:
            bindings = bind(self.env, api)
            if not isinstance(bindings, dict):
                raise TypeError("bind must return a dict from string keys to binding specs")
            if not all(isinstance(key, str) for key in bindings):
                raise TypeError("bind keys must be strings")
        except Exception as exc:
            raise BindingError("bind", str(exc)) from exc
        for key, spec in bindings.items():
            if not isinstance(spec, (GripperSpec, ActorSpec, SiteSpec)):
                exc = TypeError("expected a gripper, actor or site binding spec")
                raise BindingError(key, str(exc)) from exc
        grippers = [key for key, spec in bindings.items() if isinstance(spec, GripperSpec)]
        if len(grippers) > 1:
            exc = ValueError("bind may contain at most one gripper")
            raise BindingError("bind", str(exc)) from exc
        if self.env.robot_uids not in ("panda", "panda_wristcam"):
            raise NotImplementedError(f"unsupported robot {self.env.robot_uids!r}; expected Panda family")
        self.bindings = bindings.copy()
        self.gripper_key = grippers[0] if grippers else None
        self._official_keys: tuple[str, ...] | None = None

    def _copy(self, value: Any, dtype: torch.dtype = torch.float32) -> Tensor:
        return torch.as_tensor(value, device=self.device, dtype=dtype).detach().clone()

    def _resolve(self, value: Any) -> Any:
        return value(self.env) if callable(value) else value

    def _body(self, spec: BindingSpec) -> BodyState:
        attrs = {name: api.broadcast_reading(self._resolve(value), self.num_envs, self.device)
                 for name, value in spec.attrs.items()}
        if isinstance(spec, GripperSpec):
            agent = self.env.agent
            robot = agent.robot
            return BodyState(
                kind="gripper", pose=self._copy(agent.tcp.pose.raw_pose),
                lin_vel=self._copy(agent.tcp.linear_velocity),
                ang_vel=self._copy(agent.tcp.angular_velocity), half_size=None, attrs=attrs,
                width=self._copy(robot.get_qpos()[:, -2:].sum(-1)),
                max_width=self._copy(robot.get_qlimits()[:, -2:, 1].sum(-1)),
                arm_qvel=self._copy(robot.get_qvel()[:, :-2]),
            )
        half_size = api.normalize_half_size(self._resolve(spec.half_size), self.num_envs, self.device)
        if isinstance(spec, ActorSpec):
            actor = spec.actor
            return BodyState(kind="actor", pose=self._copy(actor.pose.raw_pose),
                             lin_vel=self._copy(actor.linear_velocity),
                             ang_vel=self._copy(actor.angular_velocity),
                             half_size=half_size, attrs=attrs)
        pose = spec.pose(self.env)
        if isinstance(pose, Pose):
            pose = pose.raw_pose
        if not isinstance(pose, Tensor) or pose.shape != (self.num_envs, 7):
            raise ValueError(f"site pose must return an [{self.num_envs}, 7] tensor or Pose")
        return BodyState(kind="site", pose=self._copy(pose),
                         lin_vel=torch.zeros(self.num_envs, 3, device=self.device),
                         ang_vel=torch.zeros(self.num_envs, 3, device=self.device),
                         half_size=half_size, attrs=attrs)

    def _contact(self, a: BindingSpec, b: BindingSpec) -> Tensor:
        if any(isinstance(spec, ActorSpec) and not spec.actor.has_collision_shapes
               for spec in (a, b)):
            return torch.zeros(self.num_envs, device=self.device)
        forces = self.env.scene.get_pairwise_contact_forces
        if isinstance(a, GripperSpec) or isinstance(b, GripperSpec):
            actor = b.actor if isinstance(a, GripperSpec) else a.actor
            agent = self.env.agent
            return self._copy(torch.linalg.vector_norm(forces(agent.finger1_link, actor), dim=-1)
                              + torch.linalg.vector_norm(forces(agent.finger2_link, actor), dim=-1))
        return self._copy(torch.linalg.vector_norm(forces(a.actor, b.actor), dim=-1))

    def snapshot(self, info: Mapping[str, Any] | None = None) -> Snapshot:
        """Read the current state after reset; official readings are float32."""
        bodies = {}
        grasping = {}
        for key, spec in self.bindings.items():
            try:
                bodies[key] = self._body(spec)
                if isinstance(spec, ActorSpec) and self.gripper_key is not None:
                    grasping[(self.gripper_key, key)] = (
                        self._copy(self.env.agent.is_grasping(spec.actor), torch.bool)
                        if spec.actor.has_collision_shapes
                        else torch.zeros(self.num_envs, device=self.device, dtype=torch.bool)
                    )
            except Exception as exc:
                raise BindingError(key, str(exc)) from exc
        contacts = {}
        physical = [(key, spec) for key, spec in self.bindings.items() if not isinstance(spec, SiteSpec)]
        for (key_a, a), (key_b, b) in combinations(physical, 2):
            try:
                contacts[(key_a, key_b)] = self._contact(a, b)
            except Exception as exc:
                raise BindingError(f"{key_a}, {key_b}", str(exc)) from exc
        evaluated = None
        if self._official_keys is None:
            evaluated = self.env.evaluate()
            self._official_keys = tuple(evaluated)
        if info is None:
            info = evaluated if evaluated is not None else self.env.evaluate()
        official = {key: api.broadcast_reading(info[key], self.num_envs, self.device)
                    for key in self._official_keys}
        return Snapshot(bodies=bodies, table_z=torch.zeros(self.num_envs, device=self.device),
                        grasping=grasping, contact_force=contacts, official=official)
