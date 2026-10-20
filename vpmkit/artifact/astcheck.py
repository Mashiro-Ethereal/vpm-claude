"""Static candidate API restrictions, not a Python security sandbox."""

import ast
from pathlib import Path

import yaml

from .literals import LiteralSyntaxError, parse_literal
from .schema import Issue


_FORBIDDEN_NAMES = {
    "eval", "exec", "compile", "open", "__import__", "globals", "locals",
    "getattr", "setattr", "delattr", "vars",
}
_FORBIDDEN_ATTRS = {
    "item", "tolist", "numpy", "cpu", "name", "_name", "_handle", "official",
    "env", "unwrapped", "scene", "agent",
}


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    return ""


def _numeric(node):
    if node is None:
        return False
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _numeric(node.operand)
    if isinstance(node, ast.Constant):
        return type(node.value) in (int, float)
    # Expressions such as math.pi / 2 are resolved by the loader's signature check.
    return True


def _progress_signature(node):
    args = node.args
    positional = args.posonlyargs + args.args
    return (
        [arg.arg for arg in positional] == ["w", "o"]
        and not args.defaults and args.vararg is None and args.kwarg is None
        and all(_numeric(default) for default in args.kw_defaults)
        and not isinstance(node, ast.AsyncFunctionDef)
    )


def _used_predicates(path):
    """Find referenced predicates; YAML/schema diagnostics belong to the loader."""
    try:
        data = yaml.safe_load((path / "stage_graph.yaml").read_text())
    except (OSError, yaml.YAMLError):
        return set()
    if not isinstance(data, dict):
        return set()
    texts = []
    stages = data.get("stages", [])
    for stage in stages if isinstance(stages, list) else []:
        if isinstance(stage, dict):
            exits = stage.get("exit", [])
            if isinstance(exits, list):
                texts.extend(exits)
            invariants = stage.get("invariants", [])
            if isinstance(invariants, list):
                texts.extend(inv.get("literal") for inv in invariants if isinstance(inv, dict))
    official = data.get("official", [])
    for decl in official if isinstance(official, list) else []:
        if isinstance(decl, dict) and isinstance(decl.get("literals"), list):
            texts.extend(decl["literals"])
    used = set()
    for text in texts:
        try:
            used.add(parse_literal(text).pred)
        except LiteralSyntaxError:
            pass
    return used


def check_candidate_ast(candidate_dir) -> list[Issue]:
    path = Path(candidate_dir)
    issues = []
    used = _used_predicates(path)
    for filename in ("predicates.py", "progress.py", "bindings.py"):
        file = path / filename
        if filename == "progress.py" and not file.exists():
            continue
        try:
            tree = ast.parse(file.read_text(), filename=str(file))
        except OSError as exc:
            issues.append(Issue("missing_file", str(exc), filename))
            continue
        except SyntaxError as exc:
            issues.append(Issue("python_syntax", str(exc), f"{filename}:{exc.lineno}"))
            continue
        bindings = filename == "bindings.py"
        allowed = {"torch", "math", "vpmkit.api", "vpmkit.geometry"}
        if bindings:
            allowed |= {"numpy", "vpmkit.world"}
        if filename == "progress.py":
            allowed.add("predicates")
        forbidden = _FORBIDDEN_NAMES - ({"getattr"} if bindings else set())
        decorators = {"predicate"}
        for node in ast.walk(tree):
            where = f"{filename}:{getattr(node, 'lineno', 1)}"
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
                for alias in node.names:
                    if alias.name == "vpmkit.api":
                        decorators.add(f"{alias.asname or alias.name}.predicate")
            elif isinstance(node, ast.ImportFrom):
                modules = [("." * node.level) + (node.module or "")]
                if node.level == 0 and node.module == "vpmkit.api":
                    decorators.update(alias.asname or alias.name for alias in node.names if alias.name == "predicate")
            for module in modules:
                # torch and numpy have useful public submodules; the vpmkit API is exact.
                root = module.split(".")[0]
                if module not in allowed and not (root in {"torch", "numpy"} and root in allowed):
                    issues.append(Issue("forbidden_import", f"Import {module!r} is not allowed", where))
            if isinstance(node, ast.Name) and node.id in forbidden:
                issues.append(Issue("forbidden_name", f"Name {node.id!r} is not allowed", where))
            if isinstance(node, ast.Attribute):
                if node.attr in forbidden or (not bindings and node.attr in _FORBIDDEN_ATTRS):
                    issues.append(Issue("forbidden_attribute", f"Attribute {node.attr!r} is not allowed", where))
        functions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        for fn in functions:
            where = f"{filename}:{fn.lineno}"
            decorated = any(
                _dotted(dec.func if isinstance(dec, ast.Call) else dec) in decorators
                for dec in fn.decorator_list
            )
            is_predicate = filename == "predicates.py" and (decorated or fn.name in used)
            is_progress = filename == "progress.py" and fn.name.startswith("progress_")
            if is_predicate and not decorated:
                issues.append(Issue("missing_decorator", f"Predicate {fn.name!r} needs @predicate", where))
            if is_predicate and isinstance(fn, ast.AsyncFunctionDef):
                issues.append(Issue("predicate_signature", "Predicates must be synchronous functions", where))
            if is_progress and not _progress_signature(fn):
                issues.append(Issue("progress_signature", f"{fn.name} must have signature (w, o, *, numeric defaults)", where))
            if is_predicate or is_progress:
                for node in ast.walk(fn):
                    if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                        issues.append(Issue("forbidden_loop", "Predicate/progress bodies cannot contain for or while statements", f"{filename}:{node.lineno}"))
        if bindings:
            bind = next((fn for fn in functions if fn.name == "bind"), None)
            if bind is None:
                issues.append(Issue("missing_bind", "bindings.py must define top-level bind(env, api)", filename))
            else:
                args = bind.args
                if ([a.arg for a in args.posonlyargs + args.args] != ["env", "api"]
                        or args.defaults or args.kwonlyargs or args.vararg or args.kwarg
                        or isinstance(bind, ast.AsyncFunctionDef)):
                    issues.append(Issue("bind_signature", "bind must have signature (env, api)", filename))
    return issues
