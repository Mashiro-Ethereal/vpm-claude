"""Read candidate function metadata without importing candidate modules."""

import ast
from dataclasses import dataclass


Function = ast.FunctionDef | ast.AsyncFunctionDef
Number = int | float


def numeric_literal(node: ast.AST | None) -> Number | None:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub)
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) in (int, float)):
        return -node.operand.value
    return None


@dataclass(frozen=True)
class Parameter:
    name: str
    kind: str
    default: ast.expr | None


def parameters(node: Function) -> list[Parameter]:
    args = node.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    result = [Parameter(arg.arg, "posonly" if i < len(args.posonlyargs) else "positional", default)
              for i, (arg, default) in enumerate(zip(positional, defaults))]
    result.extend(Parameter(arg.arg, "keyword", default)
                  for arg, default in zip(args.kwonlyargs, args.kw_defaults))
    return result


@dataclass
class FunctionInfo:
    node: Function
    module_level: bool
    params: list[Parameter]

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def line(self) -> int:
        return self.node.lineno


@dataclass
class PredicateInfo(FunctionInfo):
    decorators: list[ast.Call]
    object_params: tuple[str, ...]
    thresholds: dict[str, Number]
    keywords: dict[str, object]


@dataclass
class ProgressInfo(FunctionInfo):
    defaults: dict[str, Number]


@dataclass
class BindInfo(FunctionInfo):
    returned: ast.expr | None
    keys: list[str] | None


def _is_predicate(node: ast.expr) -> bool:
    return (isinstance(node, ast.Call)
            and ((isinstance(node.func, ast.Name) and node.func.id == "predicate")
                 or (isinstance(node.func, ast.Attribute) and node.func.attr == "predicate")))


def _defaults(params: list[Parameter]) -> dict[str, Number]:
    return {param.name: value for param in params
            if (value := numeric_literal(param.default)) is not None}


def extract_predicates(tree: ast.Module) -> list[PredicateInfo]:
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = [item for item in node.decorator_list if _is_predicate(item)]
        if not decorators:
            continue
        params = parameters(node)
        keywords: dict[str, object] = {}
        for decorator in decorators:
            for keyword in decorator.keywords:
                if keyword.arg is not None:
                    value = keyword.value
                    keywords[keyword.arg] = (value.value if isinstance(value, ast.Constant)
                                             else numeric_literal(value))
        result.append(PredicateInfo(
            node, node in tree.body, params, decorators,
            tuple(p.name for p in params[1:] if p.default is None and p.kind != "keyword"),
            _defaults(params[1:]), keywords))
    return sorted(result, key=lambda info: info.line)


def extract_progress(tree: ast.Module) -> list[ProgressInfo]:
    return [ProgressInfo(node, True, parameters(node), _defaults(parameters(node)[2:]))
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("progress_")]


def extract_bindings(tree: ast.Module) -> list[BindInfo]:
    result = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != "bind":
            continue
        last = node.body[-1]
        returned = last.value if isinstance(last, ast.Return) else None
        keys = None
        if isinstance(returned, ast.Dict) and all(
                isinstance(key, ast.Constant) and isinstance(key.value, str) for key in returned.keys):
            keys = [key.value for key in returned.keys]
        result.append(BindInfo(node, True, parameters(node), returned, keys))
    return result
