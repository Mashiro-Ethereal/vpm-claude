"""Parser for signed predicate instances."""

from dataclasses import dataclass
import re


class LiteralSyntaxError(ValueError):
    pass


@dataclass(frozen=True)
class Literal:
    pred: str
    args: tuple[str, ...]
    positive: bool = True

    @property
    def instance_key(self):
        return f"{self.pred}({', '.join(self.args)})"


_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_LITERAL = re.compile(
    rf"\s*(?P<neg>not\s+|¬\s*)?(?P<pred>{_IDENT})\s*\(\s*"
    rf"(?P<args>{_IDENT}(?:\s*,\s*{_IDENT})*)?\s*\)\s*"
)


def parse_literal(s: str) -> Literal:
    match = _LITERAL.fullmatch(s) if isinstance(s, str) else None
    if match is None:
        raise LiteralSyntaxError(f"Invalid literal: {s!r}")
    args = tuple(arg.strip() for arg in match["args"].split(",")) if match["args"] else ()
    return Literal(match["pred"], args, match["neg"] is None)
