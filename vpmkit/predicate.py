"""Predicate signatures, metadata and context-local threshold values."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import update_wrapper
from inspect import Parameter, signature
from typing import Callable, Iterator, Mapping

import torch
from torch import Tensor


@dataclass(frozen=True)
class PredicateMeta:
    name: str
    desc: str
    need_true: str
    need_false: str | None
    scale: float
    object_params: tuple[str, ...]
    thresholds: dict[str, float]


_active: ContextVar[Mapping[str, float]] = ContextVar("predicate_thresholds", default={})


@contextmanager
def active_thresholds(mapping: Mapping[str, float]) -> Iterator[None]:
    token = _active.set(mapping)
    try:
        yield
    finally:
        _active.reset(token)


class Predicate:
    def __init__(self, function: Callable, meta: PredicateMeta) -> None:
        update_wrapper(self, function)
        self.meta = meta
        self._function = function
        self._signature = signature(function)

    def __call__(self, *args, **kwargs):
        bound = self._signature.bind(*args, **kwargs)
        active = _active.get()
        for name, default in self.meta.thresholds.items():
            if name not in bound.arguments:
                bound.arguments[name] = active.get(f"{self.meta.name}.{name}", default)
        return self._function(*bound.args, **bound.kwargs)


def predicate(*, desc: str, need_true: str, need_false: str | None = None,
              scale: float) -> Callable[[Callable], Predicate]:
    for name, value in (("desc", desc), ("need_true", need_true)):
        if not isinstance(value, str) or not value.strip():
            raise TypeError(f"{name} must be a non-empty string")
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not scale > 0:
        raise TypeError("scale must be a positive int or float, not bool")

    def decorate(function: Callable) -> Predicate:
        params = list(signature(function).parameters.values())
        if (not params or params[0].name != "w"
                or params[0].kind not in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
                or params[0].default is not Parameter.empty):
            raise TypeError(f"{function.__name__}: first parameter must be w without a default")
        objects = []
        thresholds = {}
        for param in params[1:]:
            if param.kind not in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY):
                raise TypeError(f"{function.__name__}: {param.name} must not be positional-only, *args or **kwargs")
            if param.default is Parameter.empty:
                if param.kind == Parameter.KEYWORD_ONLY or thresholds:
                    raise TypeError(f"{function.__name__}: {param.name} requires a numeric default")
                objects.append(param.name)
            else:
                value = param.default
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError(f"{function.__name__}: threshold {param.name} must default to int or float, not bool")
                thresholds[param.name] = value
        if not objects:
            raise TypeError(f"{function.__name__}: at least one object parameter is required")
        return Predicate(function, PredicateMeta(function.__name__, desc, need_true,
                                                  need_false, float(scale), tuple(objects), thresholds))

    return decorate


def signed(flag: Tensor) -> Tensor:
    """Map boolean or numeric truth values to float32 margins."""
    return flag.to(torch.bool).to(torch.float32) * 2 - 1
