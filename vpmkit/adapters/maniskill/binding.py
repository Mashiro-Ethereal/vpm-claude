"""The api passed to candidate bind(env, api) functions."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import inspect
from numbers import Real
from typing import Any

import numpy as np
import torch
from torch import Tensor
from mani_skill.utils.structs.actor import Actor
from mani_skill.utils.structs.pose import Pose


_VIEW_FIELDS = {"pos", "quat", "pose", "lin_vel", "ang_vel", "half_size",
                "width", "max_width", "arm_qvel", "joint_pos", "joint_vel",
                "joint_limits", "name"}
Reading = Real | Sequence | np.ndarray | Tensor | Callable[[Any], Any]


def _validate_callable(value: Callable, label: str) -> None:
    try:
        inspect.signature(value).bind(None)
    except TypeError as exc:
        raise TypeError(f"{label} callable must accept env as its only argument") from exc


def _numeric_tensor(value: Any, label: str) -> Tensor:
    if not isinstance(value, (Real, Sequence, np.ndarray, Tensor)) or isinstance(value, (str, bytes)):
        raise TypeError(f"{label} must be a number, numeric sequence, numpy array or tensor")
    try:
        tensor = torch.as_tensor(value)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise TypeError(f"{label} must contain numeric values") from exc
    if tensor.is_complex():
        raise TypeError(f"{label} must contain real numeric values")
    return tensor


def _validate_half_size(value: Reading) -> None:
    if callable(value):
        _validate_callable(value, "half_size")
        return
    tensor = _numeric_tensor(value, "half_size")
    if tensor.ndim == 0 or tensor.shape == (3,):
        return
    if isinstance(value, Tensor) and tensor.ndim == 2 and tensor.shape[1] == 3:
        return
    raise ValueError("half_size must be a number, a length-3 vector or an [N, 3] tensor")


def _validate_attrs(attrs: dict[str, Reading]) -> None:
    for name, value in attrs.items():
        if not isinstance(name, str) or name.startswith("_") or name in _VIEW_FIELDS:
            raise ValueError(f"attribute {name!r} clashes with a view field or starts with '_' ")
        if callable(value):
            _validate_callable(value, f"attribute {name!r}")
        else:
            _numeric_tensor(value, f"attribute {name!r}")


@dataclass
class GripperSpec:
    attrs: dict[str, Reading]

    def __post_init__(self) -> None:
        _validate_attrs(self.attrs)


@dataclass
class ActorSpec:
    actor: Actor
    half_size: Reading
    attrs: dict[str, Reading]

    def __post_init__(self) -> None:
        if not isinstance(self.actor, Actor):
            raise TypeError("actor must be a mani_skill.utils.structs.actor.Actor")
        _validate_half_size(self.half_size)
        _validate_attrs(self.attrs)


@dataclass
class SiteSpec:
    pose: Callable[[Any], Tensor | Pose]
    half_size: Reading
    attrs: dict[str, Reading]

    def __post_init__(self) -> None:
        if not callable(self.pose):
            raise TypeError("site pose must be a callable taking env and returning an [N, 7] tensor or Pose")
        _validate_callable(self.pose, "site pose")
        _validate_half_size(self.half_size)
        _validate_attrs(self.attrs)


BindingSpec = GripperSpec | ActorSpec | SiteSpec


def gripper(**attrs: Reading) -> GripperSpec:
    return GripperSpec(attrs)


def actor(actor: Actor, half_size: Reading, **attrs: Reading) -> ActorSpec:
    return ActorSpec(actor, half_size, attrs)


def site(pose: Callable[[Any], Tensor | Pose], half_size: Reading = 0.0,
         **attrs: Reading) -> SiteSpec:
    return SiteSpec(pose, half_size, attrs)


def normalize_half_size(value: Any, num_envs: int, device: torch.device) -> Tensor:
    """Copy a resolved half size to float32 [N, 3]."""
    _validate_half_size(value)
    tensor = _numeric_tensor(value, "half_size").to(device=device, dtype=torch.float32)
    if tensor.ndim == 2 and tensor.shape[0] not in (1, num_envs):
        raise ValueError(f"half_size must broadcast to [{num_envs}, 3], got {tuple(tensor.shape)}")
    return tensor.expand(num_envs, 3).detach().clone()


def broadcast_reading(value: Any, num_envs: int, device: torch.device) -> Tensor:
    """Copy a reading to float32 [N, ...].

    A leading dimension of N or 1 is a batch dimension. Otherwise a new batch
    dimension is added. Use [1, ...] for a shared vector whose length equals N.
    """
    if isinstance(value, Pose):
        value = value.raw_pose
    tensor = _numeric_tensor(value, "reading").to(device=device, dtype=torch.float32)
    if tensor.ndim == 0:
        tensor = tensor.expand(num_envs)
    elif tensor.shape[0] in (1, num_envs):
        tensor = tensor.expand(num_envs, *tensor.shape[1:])
    else:
        tensor = tensor.unsqueeze(0).expand(num_envs, *tensor.shape)
    return tensor.detach().clone()
