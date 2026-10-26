"""Serializable tensor snapshots and read-only candidate views."""

from dataclasses import dataclass, fields
import json
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import torch
from torch import Tensor


_COMMON = {"pos", "quat", "pose", "lin_vel", "ang_vel"}
_JOINT = {"joint_pos", "joint_vel", "joint_limits"}
_GRIPPER = {"width", "max_width", "arm_qvel"}
_RESERVED = _COMMON | _JOINT | _GRIPPER | {"half_size", "name", "_key", "_body", "_fields"}


def _shape(value: Any, name: str, expected: tuple[int | None, ...]) -> None:
    if not isinstance(value, Tensor):
        raise ValueError(f"{name}: expected a tensor, got {type(value).__name__}")
    if len(value.shape) != len(expected) or any(
        size is not None and actual != size for actual, size in zip(value.shape, expected)
    ):
        raise ValueError(f"{name}: expected shape {expected}, got {tuple(value.shape)}")


@dataclass
class BodyState:
    kind: str
    pose: Tensor
    lin_vel: Tensor
    ang_vel: Tensor
    half_size: Tensor | None
    attrs: dict[str, Tensor]
    width: Tensor | None = None
    max_width: Tensor | None = None
    arm_qvel: Tensor | None = None
    joint_pos: Tensor | None = None
    joint_vel: Tensor | None = None
    joint_limits: Tensor | None = None

    def __post_init__(self) -> None:
        if self.kind not in ("gripper", "actor", "site"):
            raise ValueError(f"kind: expected gripper, actor or site, got {self.kind!r}")
        if not isinstance(self.attrs, dict):
            raise ValueError("attrs must be a dictionary of named tensors")
        _shape(self.pose, "pose", (None, 7))
        n = self.pose.shape[0]
        for name in ("lin_vel", "ang_vel"):
            _shape(getattr(self, name), name, (n, 3))
        if self.kind == "gripper":
            if self.half_size is not None:
                raise ValueError("half_size must be None for a gripper")
        else:
            _shape(self.half_size, "half_size", (n, 3))
        for name in _GRIPPER | _JOINT:
            value = getattr(self, name)
            if value is None:
                continue
            if name in _GRIPPER and self.kind != "gripper":
                raise ValueError(f"{name} is only allowed on a gripper")
            if name in _JOINT and self.kind == "gripper":
                raise ValueError(f"{name} is only allowed on an actor or site")
            shape = (n, None) if name == "arm_qvel" else (n, 2) if name == "joint_limits" else (n,)
            _shape(value, name, shape)
        for name, value in self.attrs.items():
            if not isinstance(name, str) or name in _RESERVED:
                raise ValueError(f"attrs name {name!r} clashes with a view field or is not a string")
            if not isinstance(value, Tensor) or value.ndim < 1 or value.shape[0] != n:
                raise ValueError(f"attrs.{name}: expected a tensor with first dimension {n}")
        for name, value in self._tensor_items():
            if value.device != self.pose.device:
                raise ValueError(f"{name}: expected device {self.pose.device}, got {value.device}")

    def _tensor_items(self) -> Iterator[tuple[str, Tensor]]:
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Tensor):
                yield field.name, value
        for name, value in self.attrs.items():
            yield f"attrs.{name}", value


def _map_tensors(value: Any, function: Callable[[Tensor], Tensor]) -> Any:
    if isinstance(value, Tensor):
        return function(value)
    if isinstance(value, dict):
        return {key: _map_tensors(child, function) for key, child in value.items()}
    return value


@dataclass
class Snapshot:
    bodies: dict[str, BodyState]
    table_z: Tensor
    grasping: dict[tuple[str, str], Tensor]
    contact_force: dict[tuple[str, str], Tensor]
    official: dict[str, Tensor]

    def __post_init__(self) -> None:
        _shape(self.table_z, "table_z", (None,))
        for name in ("bodies", "grasping", "contact_force", "official"):
            if not isinstance(getattr(self, name), dict):
                raise ValueError(f"{name} must be a dictionary")
        n = self.batch_size
        for key, body in self.bodies.items():
            if not isinstance(key, str) or not isinstance(body, BodyState):
                raise ValueError("bodies must map string keys to BodyState values")
            body.__post_init__()
        for name, pairs in (("grasping", self.grasping), ("contact_force", self.contact_force)):
            for pair, value in pairs.items():
                if not isinstance(pair, tuple) or len(pair) != 2 or not all(isinstance(x, str) for x in pair):
                    raise ValueError(f"{name}: expected a pair of string keys, got {pair!r}")
                _shape(value, f"{name}{pair}", (n,))
                if name == "grasping" and value.dtype != torch.bool:
                    raise ValueError(f"grasping{pair}: expected bool dtype, got {value.dtype}")
        for key, value in self.official.items():
            if not isinstance(key, str) or not isinstance(value, Tensor):
                raise ValueError("official must map string keys to tensors")
        for name, value in self._tensor_items():
            if value.ndim < 1 or value.shape[0] != n:
                raise ValueError(f"{name}: expected first dimension {n}, got {tuple(value.shape)}")
            if value.device != self.device:
                raise ValueError(f"{name}: expected device {self.device}, got {value.device}")

    @property
    def batch_size(self) -> int:
        return self.table_z.shape[0]

    @property
    def device(self) -> torch.device:
        return self.table_z.device

    def _tensor_items(self) -> Iterator[tuple[str, Tensor]]:
        yield "table_z", self.table_z
        for key, body in self.bodies.items():
            for name, value in body._tensor_items():
                yield f"bodies.{key}.{name}", value
        for name in ("grasping", "contact_force", "official"):
            for key, value in getattr(self, name).items():
                yield f"{name}.{key}", value

    def to(self, device: str | torch.device) -> "Snapshot":
        return self.from_dict(_map_tensors(self.to_dict(), lambda t: t.to(device)))

    def select(self, index: int | slice | Tensor) -> "Snapshot":
        if isinstance(index, int):
            if not -self.batch_size <= index < self.batch_size:
                raise IndexError(f"snapshot index {index} is out of range")
            index %= self.batch_size
            index = slice(index, index + 1)
        elif not isinstance(index, slice):
            if not isinstance(index, Tensor) or index.ndim != 1 or index.dtype not in (torch.long, torch.bool):
                raise ValueError("index must be an int, slice, 1-D LongTensor or bool mask")
        return self.from_dict(_map_tensors(self.to_dict(), lambda t: t[index]))

    @classmethod
    def cat(cls, snapshots: Sequence["Snapshot"]) -> "Snapshot":
        if not snapshots:
            raise ValueError("cat requires at least one snapshot")

        def combine(values: list[Any], path: str) -> Any:
            first = values[0]
            if isinstance(first, Tensor):
                if any(not isinstance(v, Tensor) or v.shape[1:] != first.shape[1:]
                       or v.dtype != first.dtype or v.device != first.device for v in values):
                    raise ValueError(f"{path}: snapshots must have identical tensor structure, dtype and device")
                return torch.cat(values, dim=0)
            if isinstance(first, dict):
                if any(not isinstance(v, dict) or v.keys() != first.keys() for v in values):
                    raise ValueError(f"{path}: snapshots must have identical keys")
                return {key: combine([v[key] for v in values], f"{path}.{key}") for key in first}
            if any(isinstance(v, (Tensor, dict)) or v != first for v in values):
                raise ValueError(f"{path}: snapshots must have identical structure")
            return first

        return cls.from_dict(combine([s.to_dict() for s in snapshots], "snapshot"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "vpmkit.snapshot.v1",
            "bodies": {key: {f.name: getattr(body, f.name) for f in fields(body)}
                       for key, body in self.bodies.items()},
            "table_z": self.table_z,
            "grasping": {json.dumps(pair): value for pair, value in self.grasping.items()},
            "contact_force": {json.dumps(pair): value for pair, value in self.contact_force.items()},
            "official": self.official,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Snapshot":
        if d.get("format") != "vpmkit.snapshot.v1":
            raise ValueError(f"unknown snapshot format: {d.get('format')!r}")
        return cls(bodies={key: BodyState(**body) for key, body in d["bodies"].items()},
                   table_z=d["table_z"],
                   grasping={tuple(json.loads(key)): value for key, value in d["grasping"].items()},
                   contact_force={tuple(json.loads(key)): value for key, value in d["contact_force"].items()},
                   official=d["official"])

    def save(self, path: str | Path) -> None:
        torch.save(self.to_dict(), path)

    @classmethod
    def load(cls, path: str | Path, map_location: Any = None) -> "Snapshot":
        return cls.from_dict(torch.load(path, map_location=map_location, weights_only=True))


class _ReadOnly:
    __slots__ = ()

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is read-only")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"{type(self).__name__} is read-only")


class _BodyView(_ReadOnly):
    __slots__ = ("_key", "_body")
    _fields: set[str] = _COMMON

    def __init__(self, key: str, body: BodyState) -> None:
        object.__setattr__(self, "_key", key)
        object.__setattr__(self, "_body", body)

    def __getattr__(self, name: str) -> Tensor:
        body = self._body
        if name == "pos":
            return body.pose[:, :3]
        if name == "quat":
            return body.pose[:, 3:]
        if name in self._fields:
            value = getattr(body, name)
            if value is None:
                detail = "no joint reading" if name in _JOINT else "no finger reading" if name in {"width", "max_width"} else "no arm velocity reading"
                raise AttributeError(f"object {self._key!r} has {detail} for {name}")
            return value
        if name in body.attrs:
            return body.attrs[name]
        available = sorted((self._fields - {"pos", "quat"}) & {
            f.name for f in fields(body) if getattr(body, f.name) is not None
        } | {"pos", "quat"} | body.attrs.keys())
        raise AttributeError(f"unknown attribute {name!r}; available fields: {', '.join(available)}")


class ObjectView(_BodyView):
    __slots__ = ()
    _fields = _COMMON | _JOINT | {"half_size"}


class GripperView(_BodyView):
    __slots__ = ()
    _fields = _COMMON | _GRIPPER


class World(_ReadOnly):
    __slots__ = ("_table_z", "_grasping", "_contact_force")

    def __init__(self, table_z: Tensor, grasping: dict[tuple[str, str], Tensor],
                 contact_force: dict[tuple[str, str], Tensor]) -> None:
        object.__setattr__(self, "_table_z", table_z)
        object.__setattr__(self, "_grasping", grasping)
        object.__setattr__(self, "_contact_force", contact_force)

    def __getattr__(self, name: str) -> Any:
        raise AttributeError(f"unknown attribute {name!r}; available fields: table_z, batch_size, device, grasping, contact_force")

    @property
    def table_z(self) -> Tensor:
        return self._table_z

    @property
    def batch_size(self) -> int:
        return self._table_z.shape[0]

    @property
    def device(self) -> torch.device:
        return self._table_z.device

    def grasping(self, g: GripperView, o: ObjectView) -> Tensor:
        pair = (g._key, o._key)
        if pair not in self._grasping:
            reason = ": a site cannot be grasped" if o._body.kind == "site" else ""
            raise KeyError(f"no grasp reading for ({pair[0]}, {pair[1]}){reason}")
        return self._grasping[pair]

    def contact_force(self, a: _BodyView, b: _BodyView) -> Tensor:
        pair = (a._key, b._key)
        if pair in self._contact_force:
            return self._contact_force[pair]
        if pair[::-1] in self._contact_force:
            return self._contact_force[pair[::-1]]
        raise KeyError(f"no contact force reading for ({pair[0]}, {pair[1]})")


class Objects(_ReadOnly):
    __slots__ = ("__views",)

    def __init__(self, views: dict[str, _BodyView]) -> None:
        object.__setattr__(self, "_Objects__views", views)

    def __getattr__(self, name: str) -> _BodyView:
        if name in self.__views:
            return self.__views[name]
        raise AttributeError(f"unknown object {name!r}; available fields: {', '.join(self.__views)}")


def make_views(snapshot: Snapshot) -> tuple[World, dict[str, _BodyView], Objects]:
    views = {key: (GripperView if body.kind == "gripper" else ObjectView)(key, body)
             for key, body in snapshot.bodies.items()}
    return World(snapshot.table_z, snapshot.grasping, snapshot.contact_force), views, Objects(views)
