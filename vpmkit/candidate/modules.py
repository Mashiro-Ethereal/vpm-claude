"""Load candidate modules in independent packages without writing bytecode."""

from dataclasses import dataclass
import importlib
from importlib.machinery import ModuleSpec
import inspect
from itertools import count
from pathlib import Path
import sys
from types import ModuleType
from typing import Callable

from ..predicate import Predicate
from .schema import StageGraph


@dataclass
class Candidate:
    path: Path
    graph: StageGraph
    predicates: dict[str, Predicate]
    progress: dict[str, Callable]
    bind: Callable | None


_namespaces = count()


def load_candidate_unchecked(path: str | Path) -> Candidate:
    path = Path(path).resolve()
    graph = StageGraph.from_yaml(path / "stage_graph.yaml")
    package_name = f"_vpmkit_candidate_{next(_namespaces)}"
    package = ModuleType(package_name)
    package.__path__ = [str(path)]
    package.__package__ = package_name
    package.__spec__ = ModuleSpec(package_name, loader=None, is_package=True)
    sys.modules[package_name] = package
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        predicates = importlib.import_module(f"{package_name}.predicates")
        progress = (importlib.import_module(f"{package_name}.progress")
                    if (path / "progress.py").exists() else None)
        bindings = (importlib.import_module(f"{package_name}.bindings")
                    if (path / "bindings.py").exists() else None)
    except BaseException:
        for name in list(sys.modules):
            if name == package_name or name.startswith(package_name + "."):
                del sys.modules[name]
        raise
    finally:
        sys.dont_write_bytecode = old_bytecode
    return Candidate(
        path=path, graph=graph,
        predicates={value.meta.name: value for value in vars(predicates).values()
                    if isinstance(value, Predicate)},
        progress={name.removeprefix("progress_"): value for name, value in vars(progress).items()
                  if name.startswith("progress_") and inspect.isfunction(value)
                  and value.__module__ == progress.__name__} if progress is not None else {},
        bind=getattr(bindings, "bind", None),
    )
