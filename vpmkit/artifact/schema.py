"""YAML structure and accumulated semantic diagnostics."""

from dataclasses import dataclass
from string import Formatter

from pydantic import BaseModel, ConfigDict, Field

from .literals import LiteralSyntaxError, parse_literal


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    where: str


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ObjectDecl(_Model):
    name: str


class Invariant(_Model):
    literal: str
    regress_to: str
    event: str


class Stage(_Model):
    name: str
    exit: list[str] = Field(min_length=1)
    invariants: list[Invariant] = Field(default_factory=list)


class OfficialDecl(_Model):
    literals: list[str] = Field(min_length=1)
    key: str


class ParamDecl(_Model):
    name: str
    default: float
    range: tuple[float, float]


class RuntimeCfg(_Model):
    debounce: int = Field(default=2, ge=1, strict=True)


class StageGraph(_Model):
    task: str
    objects: dict[str, ObjectDecl]
    stages: list[Stage] = Field(min_length=1)
    official: list[OfficialDecl] = Field(default_factory=list)
    params: list[ParamDecl] = Field(default_factory=list)
    runtime: RuntimeCfg = Field(default_factory=RuntimeCfg)


def check_graph(graph, predicate_specs, progress_specs) -> list[Issue]:
    issues = []

    def issue(code, message, where):
        issues.append(Issue(code, message, where))

    stage_indices = {}
    for i, stage in enumerate(graph.stages):
        if stage.name in stage_indices:
            issue("duplicate_stage", f"Duplicate stage name {stage.name!r}", f"stages[{i}].name")
        else:
            stage_indices[stage.name] = i

    tunable_predicates = set()
    param_names = set()
    available_params = {
        f"{name}.{threshold}" for name, spec in predicate_specs.items()
        for threshold in spec.thresholds
    } | {
        f"progress.{stage}.{param}" for stage, spec in progress_specs.items()
        if stage in stage_indices for param in spec.params
    }
    for i, param in enumerate(graph.params):
        where = f"params[{i}]"
        if param.name in param_names:
            issue("duplicate_param", f"Duplicate parameter {param.name!r}", where)
        param_names.add(param.name)
        if param.name not in available_params:
            issue("unknown_param", f"No threshold or progress keyword matches {param.name!r}", where)
        for name, spec in predicate_specs.items():
            if param.name in {f"{name}.{t}" for t in spec.thresholds}:
                tunable_predicates.add(name)
        lo, hi = param.range
        if lo >= hi:
            issue("invalid_range", "Parameter range must satisfy lo < hi", where)
        if not lo <= param.default <= hi:
            issue("default_out_of_range", f"Default {param.default} is outside [{lo}, {hi}]", where)

    def literal(text, where, official=False):
        try:
            lit = parse_literal(text)
        except LiteralSyntaxError as exc:
            issue("literal_syntax", str(exc), where)
            return
        spec = predicate_specs.get(lit.pred)
        if spec is None:
            issue("unknown_predicate", f"Unknown predicate {lit.pred!r}", where)
        else:
            if len(lit.args) != len(spec.obj_params):
                issue("object_arity", f"{lit.pred} expects {len(spec.obj_params)} objects, got {len(lit.args)}", where)
            if not lit.positive and spec.need_false is None:
                issue("missing_need_false", f"Negative literal requires {lit.pred}.need_false", where)
            if official and lit.pred in tunable_predicates:
                issue("official_tunable", f"Official predicate {lit.pred!r} must have fixed thresholds", where)
        for handle in lit.args:
            if handle not in graph.objects:
                issue("undefined_object", f"Undefined object handle {handle!r}", where)

    for i, stage in enumerate(graph.stages):
        for j, text in enumerate(stage.exit):
            literal(text, f"stages[{i}].exit[{j}]")
        for j, inv in enumerate(stage.invariants):
            where = f"stages[{i}].invariants[{j}]"
            literal(inv.literal, f"{where}.literal")
            target = stage_indices.get(inv.regress_to)
            if target is None or target >= i:
                issue("regress_not_earlier", f"{inv.regress_to!r} is not an earlier stage", where)
            try:
                fields = [field for _, field, _, _ in Formatter().parse(inv.event) if field is not None]
                for field in fields:
                    if field not in graph.objects:
                        issue("event_placeholder", f"Event placeholder {field!r} is not an object handle", where)
                # Also catches malformed format specifiers and nested placeholders.
                if all(field in graph.objects for field in fields):
                    inv.event.format(**{h: obj.name for h, obj in graph.objects.items()})
            except (ValueError, KeyError, IndexError, AttributeError) as exc:
                issue("event_placeholder", f"Invalid event template: {exc}", where)

    for i, decl in enumerate(graph.official):
        for j, text in enumerate(decl.literals):
            literal(text, f"official[{i}].literals[{j}]", official=True)
    return issues
