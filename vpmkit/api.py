"""Public imports for candidate files."""

from dataclasses import dataclass
import inspect
import math

from . import geometry as G
from .world import BindingAPI, ObjSpec, ObjView, WorldView, bool_margin


@dataclass(frozen=True)
class PredicateSpec:
    name: str
    desc: str
    need_true: str
    need_false: str | None
    scale: float
    obj_params: tuple[str, ...]
    thresholds: dict[str, float]


@dataclass(frozen=True)
class ProgressSpec:
    name: str
    params: dict[str, float]


def _signature(fn, prefix):
    parameters = list(inspect.signature(fn).parameters.values())
    positional = (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    for i, name in enumerate(prefix):
        if (len(parameters) <= i or parameters[i].name != name
                or parameters[i].kind not in positional
                or parameters[i].default is not inspect.Parameter.empty):
            raise ValueError(f"{fn.__name__}: signature must start with ({', '.join(prefix)}) without defaults")
    return parameters[len(prefix):], positional


def _numeric_default(fn, p):
    if type(p.default) not in (int, float) or not math.isfinite(p.default):
        raise ValueError(f"{fn.__name__}: {p.name} must have a finite int/float default")
    return float(p.default)


def predicate(*, desc: str, need_true: str, need_false: str | None = None, scale: float = 1.0):
    """Declare object arguments and keyword-only numeric thresholds."""
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("predicate scale must be finite and positive")

    def decorate(fn):
        parameters, positional = _signature(fn, ("w",))
        objects, thresholds = [], {}
        for p in parameters:
            if p.kind in positional and p.default is inspect.Parameter.empty:
                objects.append(p.name)
            elif p.kind == inspect.Parameter.KEYWORD_ONLY:
                thresholds[p.name] = _numeric_default(fn, p)
            else:
                raise ValueError(f"{fn.__name__}: invalid parameter {p.name!r}; use required objects or keyword-only thresholds")
        fn.__vpm_predicate__ = PredicateSpec(
            fn.__name__, desc, need_true, need_false, float(scale), tuple(objects), thresholds,
        )
        return fn
    return decorate


def _progress_spec(fn, stage):
    parameters, _ = _signature(fn, ("w", "o"))
    params = {}
    for p in parameters:
        if p.kind != inspect.Parameter.KEYWORD_ONLY:
            raise ValueError(f"{fn.__name__}: progress parameters must be keyword-only")
        params[p.name] = _numeric_default(fn, p)
    return ProgressSpec(stage, params)


__all__ = ["predicate", "PredicateSpec", "ProgressSpec", "bool_margin", "G",
           "ObjView", "WorldView", "ObjSpec", "BindingAPI"]
