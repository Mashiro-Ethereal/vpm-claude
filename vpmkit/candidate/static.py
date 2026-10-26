"""Parse, schema and code-restriction checks that never execute candidate code."""

import ast
from collections import Counter
from pathlib import Path
import re

from pydantic import ValidationError
import yaml

from ..literal import Literal, LiteralSyntaxError, parse_literal
from .pyinfo import (FunctionInfo, PredicateInfo, extract_bindings, extract_predicates,
                     extract_progress, numeric_literal)
from .report import GROUPS, Problem, Report
from .schema import StageGraph


def _yaml_location(parts: tuple[str | int, ...] | str) -> str:
    if isinstance(parts, str):
        path = parts
    else:
        path = ""
        for part in parts:
            if part == "[key]":
                continue
            path += f"[{part}]" if isinstance(part, int) else ("." if path else "") + part
    return "stage_graph.yaml" + (f": {path}" if path else "")


def _parse(path: Path, problems: list[Problem]) -> tuple[object, dict[str, ast.Module]]:
    for name in ("stage_graph.yaml", "bindings.py", "predicates.py", "notes.md"):
        if not (path / name).is_file():
            problems.append(Problem("parse.missing_file", name, f"Required file {name} is missing."))
    data = None
    if (path / "stage_graph.yaml").is_file():
        try:
            data = yaml.safe_load((path / "stage_graph.yaml").read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            location = f"stage_graph.yaml:{mark.line + 1}:{mark.column + 1}" if mark else "stage_graph.yaml"
            problems.append(Problem("parse.yaml", location, str(exc)))
    trees = {}
    for file in sorted(path.rglob("*.py")):
        relative = file.relative_to(path)
        if "__pycache__" in relative.parts or not file.is_file():
            continue
        name = relative.as_posix()
        try:
            trees[name] = ast.parse(file.read_text(encoding="utf-8"), filename=name)
        except SyntaxError as exc:
            problems.append(Problem("parse.python", f"{name}:{exc.lineno or 1}", exc.msg))
    return data, trees


def _signature_errors(info: FunctionInfo, predicate: bool) -> list[str]:
    errors = []
    args, params = info.node.args, info.params
    if isinstance(info.node, ast.AsyncFunctionDef):
        errors.append("must be a synchronous function")
    if not info.module_level:
        errors.append("must be defined at module level")
    if args.vararg or args.kwarg:
        errors.append("*args and **kwargs are not allowed")
    if predicate:
        if args.posonlyargs:
            errors.append("positional-only parameters are not allowed")
        if not params or params[0].name != "w" or params[0].kind != "positional" or params[0].default is not None:
            errors.append("first parameter must be w without a default")
        objects = [p for p in params[1:] if p.kind != "keyword" and p.default is None]
        if not objects:
            errors.append("at least one object parameter without a default is required")
        thresholds = [p for p in params[1:] if p.default is not None or p.kind == "keyword"]
    else:
        if (len(params) < 2 or [p.name for p in params[:2]] != ["w", "o"]
                or any(p.kind == "keyword" or p.default is not None for p in params[:2])):
            errors.append("first parameters must be (w, o) without defaults")
        thresholds = params[2:]
    for param in thresholds:
        if param.kind == "posonly":
            errors.append(f"parameter {param.name} must accept a keyword argument")
        if numeric_literal(param.default) is None:
            errors.append(f"parameter {param.name} requires a numeric literal default (not bool)")
    return errors


def _check_bindings(tree: ast.Module, objects: set[str], problems: list[Problem]) -> None:
    bindings = extract_bindings(tree)
    if len(bindings) != 1:
        problems.append(Problem("schema.binding_keys", f"bindings.py:{bindings[-1].line if bindings else 1}",
                                "Define exactly one module-level def bind(env, api)."))
    for info in bindings:
        if (isinstance(info.node, ast.AsyncFunctionDef) or info.node.args.vararg or info.node.args.kwarg
                or [(p.name, p.kind, p.default) for p in info.params]
                != [("env", "positional", None), ("api", "positional", None)]):
            problems.append(Problem("schema.binding_keys", f"bindings.py:{info.line}",
                                    "The binding signature must be def bind(env, api)."))
        location = f"bindings.py:{info.node.body[-1].lineno}"
        if info.keys is None:
            problems.append(Problem("schema.binding_keys", location,
                                    "bind must end with return of a dict literal with string keys, without unpacking."))
            continue
        messages = []
        missing, extra = objects - set(info.keys), set(info.keys) - objects
        duplicates = sorted(key for key, count in Counter(info.keys).items() if count > 1)
        if missing:
            messages.append(f"missing keys: {', '.join(sorted(missing))}")
        if extra:
            messages.append(f"extra keys: {', '.join(sorted(extra))}")
        if duplicates:
            messages.append(f"duplicate keys: {', '.join(duplicates)}")
        if messages:
            problems.append(Problem("schema.binding_keys", location, "; ".join(messages)))


def _check_templates(info: PredicateInfo, used: bool, negated: bool, problems: list[Problem]) -> None:
    if used:
        errors = []
        required = ["desc", "need_true"] + (["need_false"] if negated else [])
        for name in required:
            value = info.keywords.get(name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} must be a non-empty string literal")
        scale = info.keywords.get("scale")
        if type(scale) not in (int, float) or not scale > 0:
            errors.append("scale must be a positive numeric literal")
        for decorator in info.decorators:
            if decorator.args:
                errors.append("predicate accepts keyword arguments only")
            for keyword in decorator.keywords:
                if keyword.arg not in {"desc", "need_true", "need_false", "scale"}:
                    errors.append(f"unexpected decorator keyword: {keyword.arg or '**unpacking'}")
        if errors:
            problems.append(Problem("schema.template", f"predicates.py:{info.decorators[0].lineno}",
                                    "; ".join(errors)))
    for decorator in info.decorators:
        for keyword in decorator.keywords:
            if keyword.arg not in {"need_true", "need_false"} or not isinstance(keyword.value, ast.Constant):
                continue
            value = keyword.value.value
            if not isinstance(value, str):
                continue
            pattern = r"\{([^{}]*)\}"
            remainder = re.sub(pattern, "", value)
            if ("{" in remainder or "}" in remainder
                    or any(name not in info.object_params for name in re.findall(pattern, value))):
                problems.append(Problem("schema.template_placeholder", f"predicates.py:{keyword.lineno}",
                                        f"{keyword.arg} must use only object placeholders: "
                                        + ", ".join("{" + name + "}" for name in info.object_params)))


def _schema(data: object, trees: dict[str, ast.Module], problems: list[Problem]) -> None:
    try:
        graph = StageGraph.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            problems.append(Problem("schema.format", _yaml_location(error["loc"]),
                                    error["msg"].removeprefix("Value error, ")))
        return
    predicates = extract_predicates(trees["predicates.py"])
    by_name = {info.name: info for info in predicates}
    progress = extract_progress(trees["progress.py"]) if "progress.py" in trees else []
    definitions = Counter(node.name for node in trees["predicates.py"].body
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    for info in predicates:
        errors = _signature_errors(info, predicate=True)
        if definitions[info.name] > 1 or len(info.decorators) > 1:
            errors.append("predicate must be defined and decorated exactly once")
        if errors:
            problems.append(Problem("schema.predicate_signature", f"predicates.py:{info.line}",
                                    f"{info.name}: " + "; ".join(errors)))
    stage_indices = {stage.name: i for i, stage in enumerate(graph.stages)}
    for info in progress:
        errors = _signature_errors(info, predicate=False)
        if info.name.removeprefix("progress_") not in stage_indices:
            errors.append("function must name an existing stage")
        if errors:
            problems.append(Problem("schema.progress_signature", f"progress.py:{info.line}",
                                    f"{info.name}: " + "; ".join(errors)))
    _check_bindings(trees["bindings.py"], set(graph.objects), problems)

    literals: dict[str, Literal] = {}
    used, official, negated = set(), set(), set()

    def read_literal(text: str, path: str, is_official: bool = False) -> None:
        location = _yaml_location(path)
        try:
            literal = parse_literal(text)
        except LiteralSyntaxError as exc:
            problems.append(Problem("schema.literal_syntax", location, str(exc)))
            return
        literals[path] = literal
        used.add(literal.predicate)
        if is_official:
            official.add(literal.predicate)
        if literal.negated:
            negated.add(literal.predicate)
        info = by_name.get(literal.predicate)
        if info is None:
            problems.append(Problem("schema.unknown_predicate", location,
                                    f"Unknown predicate {literal.predicate!r}."))
        elif len(literal.args) != len(info.object_params):
            problems.append(Problem("schema.arity", location,
                                    f"{info.name} expects {len(info.object_params)} objects; got {len(literal.args)}."))
        for arg in literal.args:
            if arg not in graph.objects:
                problems.append(Problem("schema.unknown_object", location, f"Unknown object {arg!r}."))

    guards: list[set[Literal]] = []
    for i, stage in enumerate(graph.stages):
        for j, text in enumerate(stage.exit):
            read_literal(text, f"stages[{i}].exit[{j}]")
        for j, invariant in enumerate(stage.invariants):
            read_literal(invariant.literal, f"stages[{i}].invariants[{j}].literal")
        guards.append({literals[path] for j in range(len(stage.exit))
                       if (path := f"stages[{i}].exit[{j}]") in literals})
    for i, entry in enumerate(graph.official):
        for j, text in enumerate(entry.literals):
            read_literal(text, f"official[{i}].literals[{j}]", is_official=True)

    for i, stage in enumerate(graph.stages):
        if not stage.exit:
            problems.append(Problem("schema.empty_guard", _yaml_location(f"stages[{i}].exit"),
                                    "Stage requires at least one exit literal."))
        seen: set[Literal] = set()
        for j in range(len(stage.exit)):
            path = f"stages[{i}].exit[{j}]"
            literal = literals.get(path)
            if literal is None:
                continue
            opposite = Literal(literal.predicate, literal.args, not literal.negated)
            if opposite in seen:
                problems.append(Problem("schema.guard_contradiction", _yaml_location(path),
                                        f"Guard contains both {literal} and {opposite}."))
            seen.add(literal)
        for j, invariant in enumerate(stage.invariants):
            path = f"stages[{i}].invariants[{j}]"
            target = stage_indices.get(invariant.regress_to)
            valid_target = target is not None and target < i
            if not valid_target:
                problems.append(Problem("schema.regress_target", _yaml_location(path + ".regress_to"),
                                        f"Target {invariant.regress_to!r} must name a stage before {stage.name!r}."))
            literal = literals.get(path + ".literal")
            if literal is None:
                continue
            opposite = Literal(literal.predicate, literal.args, not literal.negated)
            if opposite in guards[i]:
                problems.append(Problem("schema.invariant_conflict", _yaml_location(path + ".literal"),
                                        f"Invariant {literal} contradicts guard {opposite}."))
            if valid_target and not any(literal in guards[u] for u in range(target, i)):
                problems.append(Problem("schema.regress_too_late", _yaml_location(path + ".regress_to"),
                                        f"No exit from {invariant.regress_to!r} through the preceding stage establishes {literal}."))

    keys: set[str] = set()
    success = []
    for i, entry in enumerate(graph.official):
        if not entry.literals:
            problems.append(Problem("schema.official_format", _yaml_location(f"official[{i}].literals"),
                                    "Official entry requires at least one literal."))
        if entry.key in keys:
            problems.append(Problem("schema.official_format", _yaml_location(f"official[{i}].key"),
                                    f"Duplicate official key {entry.key!r}."))
        keys.add(entry.key)
        if entry.key == "success":
            success.append(i)
    if not success:
        problems.append(Problem("schema.success", _yaml_location("official"), "An official success entry is required."))
    last = len(graph.stages) - 1
    final_paths = ([f"stages[{last}].exit[{j}]" for j in range(len(graph.stages[last].exit))]
                   + [f"stages[{last}].invariants[{j}].literal" for j in range(len(graph.stages[last].invariants))])
    for i in success:
        paths = [f"official[{i}].literals[{j}]" for j in range(len(graph.official[i].literals))]
        if all(path in literals for path in paths + final_paths):
            expected, actual = {literals[p] for p in final_paths}, {literals[p] for p in paths}
            if actual != expected:
                problems.append(Problem("schema.success", _yaml_location(f"official[{i}].literals"),
                                        "Success must equal the last exit plus invariants; "
                                        f"missing: {sorted(map(str, expected - actual))}; "
                                        f"extra: {sorted(map(str, actual - expected))}."))

    defaults: dict[str, int | float | None] = {}
    required: set[str] = set()
    for info in predicates:
        _check_templates(info, info.name in used, info.name in negated, problems)
        if info.name in used:
            for param in info.params[1:]:
                if param.default is not None:
                    name = f"{info.name}.{param.name}"
                    defaults[name] = numeric_literal(param.default)
                    if info.name not in official:
                        required.add(name)
    for info in progress:
        for param in info.params[2:]:
            name = f"progress.{info.name.removeprefix('progress_')}.{param.name}"
            defaults[name] = numeric_literal(param.default)
            required.add(name)
    for i, param in enumerate(graph.params):
        path = f"params[{i}]"
        if any(param.name.startswith(p + ".") for p in official):
            problems.append(Problem("schema.official_threshold", _yaml_location(path + ".name"),
                                    f"Official predicate parameter {param.name!r} must not be tunable."))
        elif param.name not in defaults:
            problems.append(Problem("schema.param_unknown", _yaml_location(path + ".name"),
                                    f"Unknown or unused parameter {param.name!r}."))
        low, high = param.range
        if not low < high:
            problems.append(Problem("schema.param_value", _yaml_location(path + ".range"), "Range must have low < high."))
        if not low <= param.default <= high:
            problems.append(Problem("schema.param_value", _yaml_location(path + ".default"), "Default must lie in the range."))
        expected = defaults.get(param.name)
        if expected is not None and param.default != expected:
            problems.append(Problem("schema.param_value", _yaml_location(path + ".default"),
                                    f"Default must equal signature default {expected!r}; got {param.default!r}."))
    for name in sorted(required - {param.name for param in graph.params}):
        problems.append(Problem("schema.param_missing", _yaml_location("params"), f"Declare parameter {name!r}."))


_UNSAFE_MODULES = {
    "os", "sys", "io", "pathlib", "shutil", "glob", "tempfile", "pickle", "shelve", "subprocess",
    "multiprocessing", "threading", "socket", "urllib", "http", "requests", "importlib", "ctypes", "builtins",
}
_UNSAFE_NAMES = {"open", "exec", "eval", "compile", "__import__"}
_LOOPS = (ast.For, ast.AsyncFor, ast.While, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _allowed_import(module: str) -> bool:
    return module == "torch" or module.startswith("torch.") or module in {"math", "vpmkit.api"}


def _identifiers(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, ast.alias):
        return node.name.split(".") + ([node.asname] if node.asname else [])
    if isinstance(node, ast.ImportFrom):
        return (node.module or "").split(".")
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.arg):
        return [node.arg]
    if isinstance(node, ast.keyword) and node.arg:
        return [node.arg]
    return []


def _restrictions(trees: dict[str, ast.Module], problems: list[Problem]) -> None:
    for file, tree in trees.items():
        restricted = file in {"predicates.py", "progress.py"}
        for node in sorted(ast.walk(tree), key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))):
            location = f"{file}:{getattr(node, 'lineno', 1)}"
            imports: list[tuple[str, int]] = []
            if isinstance(node, ast.Import):
                imports = [(alias.name, alias.lineno) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [(node.module or "", node.lineno)]
            for module, line in imports:
                allowed = _allowed_import(module)
                if isinstance(node, ast.ImportFrom) and node.level:
                    allowed = file == "progress.py" and node.level == 1 and module == "predicates"
                if restricted and not allowed:
                    problems.append(Problem("ast.import", f"{file}:{line}", f"Import {module!r} is not allowed in {file}."))
                if module.split(".")[0] in _UNSAFE_MODULES:
                    problems.append(Problem("ast.unsafe", f"{file}:{line}", f"Import of {module!r} is forbidden."))
            if restricted:
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in {"item", "tolist", "numpy", "cpu"}):
                    problems.append(Problem("ast.host_transfer", location, f"Call to .{node.func.attr}() is forbidden."))
                if isinstance(node, _LOOPS):
                    problems.append(Problem("ast.loop", location, "Loops and comprehensions are forbidden."))
            if (file == "predicates.py" and isinstance(node, ast.Attribute)
                    and node.attr == "name" and isinstance(node.ctx, ast.Load)):
                problems.append(Problem("ast.name_access", location, "Reading .name is forbidden in predicates.py."))
            for name in _identifiers(node):
                if ((isinstance(node, ast.Name) and name in _UNSAFE_NAMES)
                        or (name.startswith("__") and name.endswith("__"))):
                    problems.append(Problem("ast.unsafe", location, f"Identifier {name!r} is forbidden."))


def check_static(path: str | Path) -> Report:
    """Check a candidate directory using YAML and Python syntax trees only."""
    path = Path(path)
    report = Report(str(path), dict.fromkeys(GROUPS, "skipped"), [])
    data, trees = _parse(path, report.problems)
    report.groups["parse"] = "failed" if report.problems else "passed"
    if report.problems:
        return report
    _schema(data, trees, report.problems)
    report.groups["schema"] = "failed" if report.problems else "passed"
    if report.problems:
        return report
    _restrictions(trees, report.problems)
    report.groups["ast"] = "failed" if report.problems else "passed"
    return report
