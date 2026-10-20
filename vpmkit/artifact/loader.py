"""Load candidate artifacts without executing simulator bindings."""

from dataclasses import dataclass, replace
import importlib.util
import inspect
from itertools import count
import math
from pathlib import Path
import sys

from pydantic import ValidationError
import yaml

from ..api import PredicateSpec, ProgressSpec, _progress_spec
from .astcheck import check_candidate_ast
from .schema import Issue, StageGraph, check_graph


class CandidateError(ValueError):
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        super().__init__("\n".join(f"{i.where}: [{i.code}] {i.message}" for i in issues))


@dataclass
class Candidate:
    graph: StageGraph
    dir: Path
    predicates: dict[str, object]
    predicate_specs: dict[str, PredicateSpec]
    progress: dict[str, object]
    progress_specs: dict[str, ProgressSpec]
    bind: object
    params: dict[str, float]

    @property
    def display_names(self):
        return {handle: obj.name for handle, obj in self.graph.objects.items()}

    def with_params(self, overrides) -> "Candidate":
        declarations = {param.name: param for param in self.graph.params}
        issues, values = [], dict(self.params)
        for name, value in overrides.items():
            if name not in declarations:
                issues.append(Issue("unknown_param", f"Unknown tunable parameter {name!r}", "params"))
                continue
            lo, hi = declarations[name].range
            if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
                issues.append(Issue("param_out_of_range", f"{name} must be a finite number in [{lo}, {hi}]", "params"))
            else:
                values[name] = float(value)
        if issues:
            raise CandidateError(issues)
        return replace(self, params=values)


_LOAD_IDS = count()


def _import_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_candidate(path) -> Candidate:
    path = Path(path).resolve()
    issues = []
    graph = None
    try:
        graph = StageGraph.model_validate(yaml.safe_load((path / "stage_graph.yaml").read_text()))
    except (OSError, yaml.YAMLError) as exc:
        issues.append(Issue("yaml_error", str(exc), "stage_graph.yaml"))
    except ValidationError as exc:
        issues.extend(Issue("schema", error["msg"], ".".join(map(str, error["loc"])) or "stage_graph.yaml")
                      for error in exc.errors())
    issues.extend(check_candidate_ast(path))
    if issues:
        raise CandidateError(issues)

    prefix = f"_vpm_candidate_{next(_LOAD_IDS)}"
    modules = {}
    sentinel = object()
    previous_predicates = sys.modules.get("predicates", sentinel)
    previous_path = sys.path[:]
    try:
        for filename in ("predicates", "progress", "bindings"):
            if filename == "progress" and not (path / "progress.py").exists():
                continue
            if filename == "progress" and "predicates" not in modules:
                continue
            try:
                if filename == "progress":
                    sys.modules["predicates"] = modules["predicates"]
                modules[filename] = _import_file(path / f"{filename}.py", f"{prefix}_{filename}")
            except Exception as exc:
                issues.append(Issue("import_error", f"{type(exc).__name__}: {exc}", f"{filename}.py"))
            finally:
                if previous_predicates is sentinel:
                    sys.modules.pop("predicates", None)
                else:
                    sys.modules["predicates"] = previous_predicates
                sys.path[:] = previous_path
    finally:
        for filename in ("predicates", "progress", "bindings"):
            sys.modules.pop(f"{prefix}_{filename}", None)

    predicates = {
        name: fn for name, fn in vars(modules["predicates"]).items()
        if inspect.isfunction(fn) and hasattr(fn, "__vpm_predicate__")
    } if "predicates" in modules else {}
    predicate_specs = {name: fn.__vpm_predicate__ for name, fn in predicates.items()}
    progress, progress_specs = {}, {}
    if "progress" in modules:
        for name, fn in vars(modules["progress"]).items():
            if (name.startswith("progress_") and inspect.isfunction(fn)
                    and fn.__module__ == modules["progress"].__name__):
                stage = name[len("progress_"):]
                try:
                    progress_specs[stage] = _progress_spec(fn, stage)
                    progress[stage] = fn
                except ValueError as exc:
                    issues.append(Issue("progress_signature", str(exc), "progress.py"))
    issues.extend(check_graph(graph, predicate_specs, progress_specs))
    if issues:
        raise CandidateError(issues)
    return Candidate(
        graph, path, predicates, predicate_specs, progress, progress_specs,
        modules["bindings"].bind, {p.name: p.default for p in graph.params},
    )
