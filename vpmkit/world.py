"""Simulator-independent world tensors and candidate-facing views."""

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Sequence

import torch
from torch import Tensor


def bool_margin(b: Tensor) -> Tensor:
    """Map a boolean tensor to float32 margins (+1 true, -1 false)."""
    if not isinstance(b, Tensor) or b.dtype != torch.bool:
        raise TypeError("bool_margin expects a boolean tensor")
    return b.to(dtype=torch.float32) * 2.0 - 1.0


@dataclass
class ObjState:
    pos: Tensor
    quat: Tensor
    linvel: Tensor
    angvel: Tensor
    half_size: Tensor
    kind: str
    attrs: dict[str, Tensor] = field(default_factory=dict)


_OBJECT_FIELDS = ("pos", "quat", "linvel", "angvel", "half_size")


@dataclass
class WorldState:
    N: int
    device: torch.device | str
    objects: dict[str, ObjState]
    grasping: dict[tuple[str, str], Tensor] = field(default_factory=dict)
    contacts: dict[tuple[str, str], Tensor] = field(default_factory=dict)
    official: dict[str, Tensor] = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def __post_init__(self):
        self.device = torch.device(self.device)

    def to_dict(self) -> dict:
        """Plain tensors and containers for torch.save (no WorldState/ObjState objects)."""
        return {
            "N": self.N, "device": str(self.device),
            "objects": {
                name: {**{key: getattr(obj, key) for key in _OBJECT_FIELDS},
                       "kind": obj.kind, "attrs": dict(obj.attrs)}
                for name, obj in self.objects.items()
            },
            **{key: dict(getattr(self, key))
               for key in ("grasping", "contacts", "official", "meta")},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldState":
        objects = {name: ObjState(**obj) for name, obj in data["objects"].items()}
        # torch.load(map_location=...) can change the saved tensor device.
        tensors = [obj.pos for obj in objects.values()] or list(data["official"].values())
        device = tensors[0].device if tensors else data["device"]
        return cls(data["N"], device, objects,
                   **{key: dict(data[key]) for key in ("grasping", "contacts", "official", "meta")})

    def _map(self, transform, n, device):
        objects = {
            name: ObjState(
                **{key: transform(getattr(obj, key)) for key in _OBJECT_FIELDS},
                kind=obj.kind,
                attrs={key: transform(t) for key, t in obj.attrs.items()},
            )
            for name, obj in self.objects.items()
        }
        return WorldState(
            n, device, objects,
            **{key: {k: transform(t) for k, t in getattr(self, key).items()}
               for key in ("grasping", "contacts", "official")},
            meta=dict(self.meta),
        )

    def to(self, device) -> "WorldState":
        device = torch.device(device)
        result = self._map(lambda t: t.to(device), self.N, device)
        # Resolve an unindexed CUDA device to the actual tensor device.
        if result.objects:
            result.device = next(iter(result.objects.values())).pos.device
        return result

    def index(self, idx: Tensor) -> "WorldState":
        if not isinstance(idx, Tensor) or idx.ndim != 1 or idx.dtype not in (torch.long, torch.bool):
            raise ValueError("index must be a one-dimensional LongTensor or BoolTensor")
        if idx.dtype == torch.bool and idx.shape != (self.N,):
            raise ValueError(f"boolean index must have shape [{self.N}]")
        idx = idx.to(self.device)
        n = int(idx.sum()) if idx.dtype == torch.bool else idx.numel()
        return self._map(lambda t: t[idx], n, self.device)

    @staticmethod
    def cat(worlds: list["WorldState"]) -> "WorldState":
        """Concatenate tensors with matching keys; retain the first world's metadata."""
        if not worlds:
            raise ValueError("WorldState.cat requires at least one world")
        first = worlds[0]
        for world in worlds:
            world.validate()
            if world.device != first.device:
                raise ValueError("WorldState.cat requires the same device")
            for key in ("objects", "grasping", "contacts", "official"):
                if getattr(world, key).keys() != getattr(first, key).keys():
                    raise ValueError(f"WorldState.cat requires matching {key} keys")
            for name, obj in world.objects.items():
                ref = first.objects[name]
                if obj.kind != ref.kind or obj.attrs.keys() != ref.attrs.keys():
                    raise ValueError(f"WorldState.cat requires matching kind and attrs for {name!r}")
        objects = {
            name: ObjState(
                **{key: torch.cat([getattr(w.objects[name], key) for w in worlds])
                   for key in _OBJECT_FIELDS},
                kind=obj.kind,
                attrs={key: torch.cat([w.objects[name].attrs[key] for w in worlds])
                       for key in obj.attrs},
            )
            for name, obj in first.objects.items()
        }
        return WorldState(
            sum(w.N for w in worlds), first.device, objects,
            **{key: {k: torch.cat([getattr(w, key)[k] for w in worlds])
                     for k in getattr(first, key)}
               for key in ("grasping", "contacts", "official")},
            meta=dict(first.meta),
        )

    def validate(self) -> None:
        if type(self.N) is not int or self.N < 0:
            raise ValueError("N must be a nonnegative integer")

        def check(t, label, shape=None, dtype=None, floating=False):
            if not isinstance(t, Tensor):
                raise ValueError(f"{label} must be a tensor")
            if t.ndim == 0 or t.shape[0] != self.N:
                raise ValueError(f"{label} must have leading dimension N={self.N}")
            if shape is not None and tuple(t.shape) != shape:
                raise ValueError(f"{label} must have shape {shape}, got {tuple(t.shape)}")
            if t.device.type != self.device.type or (
                self.device.index is not None and t.device.index != self.device.index
            ):
                raise ValueError(f"{label} must be on {self.device}, got {t.device}")
            if dtype is not None and t.dtype != dtype:
                raise ValueError(f"{label} must have dtype {dtype}")
            if floating and not t.is_floating_point():
                raise ValueError(f"{label} must have a floating-point dtype")

        for name, obj in self.objects.items():
            if obj.kind not in {"actor", "site", "gripper", "table"}:
                raise ValueError(f"objects[{name!r}].kind is invalid: {obj.kind!r}")
            for key in _OBJECT_FIELDS:
                check(getattr(obj, key), f"{name}.{key}", (self.N, 4 if key == "quat" else 3), floating=True)
            for key, t in obj.attrs.items():
                check(t, f"{name}.attrs[{key!r}]")
            if obj.kind == "gripper":
                for key in ("width", "arm_qvel"):
                    if key not in obj.attrs:
                        raise ValueError(f"gripper {name!r} is missing attr {key!r}")
                check(obj.attrs["width"], f"{name}.width", (self.N,), floating=True)
                check(obj.attrs["arm_qvel"], f"{name}.arm_qvel", floating=True)
                if obj.attrs["arm_qvel"].ndim != 2:
                    raise ValueError(f"{name}.arm_qvel must have shape [N, D]")
        for pair, t in self.grasping.items():
            if len(pair) != 2 or any(h not in self.objects for h in pair):
                raise ValueError(f"grasping key {pair!r} must reference two object handles")
            if self.objects[pair[0]].kind != "gripper":
                raise ValueError(f"grasping key {pair!r} must start with a gripper")
            check(t, f"grasping[{pair!r}]", (self.N,), torch.bool)
        for pair, t in self.contacts.items():
            if len(pair) != 2 or any(h not in self.objects for h in pair):
                raise ValueError(f"contact key {pair!r} must reference two object handles")
            if pair[0] != pair[1] and pair[::-1] in self.contacts:
                raise ValueError(f"contact pair {pair!r} is stored in both orders")
            check(t, f"contacts[{pair!r}]", (self.N,), floating=True)
        for key, t in self.official.items():
            check(t, f"official[{key!r}]")


class ObjView:
    """Read-only attributes over an object's tensors (tensors are not copied)."""

    __slots__ = ("_state", "_handle")

    def __init__(self, state: ObjState, handle: str):
        self._state = state
        self._handle = handle

    @property
    def pos(self):
        return self._state.pos

    @property
    def quat(self):
        return self._state.quat

    @property
    def linvel(self):
        return self._state.linvel

    @property
    def angvel(self):
        return self._state.angvel

    @property
    def half_size(self):
        return self._state.half_size

    @property
    def kind(self):
        return self._state.kind

    def attr(self, key):
        try:
            return self._state.attrs[key]
        except KeyError:
            raise KeyError(f"object has no attribute {key!r}") from None

    @property
    def width(self):
        if self.kind != "gripper":
            raise AttributeError("width is only available for grippers")
        return self.attr("width")

    @property
    def arm_qvel(self):
        if self.kind != "gripper":
            raise AttributeError("arm_qvel is only available for grippers")
        return self.attr("arm_qvel")


class WorldView:
    __slots__ = ("_world",)

    def __init__(self, world: WorldState):
        self._world = world

    @property
    def N(self):
        return self._world.N

    @property
    def device(self):
        return self._world.device

    def grasping(self, g: ObjView, o: ObjView) -> Tensor:
        return self._world.grasping[g._handle, o._handle]

    def contact_force(self, a: ObjView, b: ObjView) -> Tensor:
        pair = (a._handle, b._handle)
        if pair not in self._world.contacts:
            pair = pair[::-1]
        return self._world.contacts[pair]

    bool_margin = staticmethod(bool_margin)


@dataclass
class ObjSpec:
    kind: str
    source: Any
    half_size: Tensor | float | Sequence[float] | Callable[[], Any] | None = None
    attrs: dict[str, Tensor | Callable[[], Tensor]] = field(default_factory=dict)


class BindingAPI(Protocol):
    def gripper(self) -> ObjSpec: ...

    def actor(self, actor, half_size, attrs=None) -> ObjSpec: ...

    def site(self, source, attrs=None) -> ObjSpec: ...

    def table(self) -> ObjSpec: ...
