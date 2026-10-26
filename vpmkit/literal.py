"""Parsing and canonical formatting of predicate literals."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Literal:
    predicate: str
    args: tuple[str, ...]
    negated: bool

    @property
    def instance(self) -> tuple[str, tuple[str, ...]]:
        return self.predicate, self.args

    @property
    def instance_text(self) -> str:
        return f"{self.predicate}({', '.join(self.args)})"

    def __str__(self) -> str:
        return ("not " if self.negated else "") + self.instance_text


class LiteralSyntaxError(ValueError):
    """A string is not a single predicate literal."""


_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_LITERAL = re.compile(rf"\s*(?P<not>not\s+)?(?P<pred>{_IDENT})\s*\(\s*"
                      rf"(?P<args>{_IDENT}(?:\s*,\s*{_IDENT})*)\s*\)\s*")


def parse_literal(text: str) -> Literal:
    match = _LITERAL.fullmatch(text) if isinstance(text, str) else None
    if match is None:
        raise LiteralSyntaxError(f"Invalid literal: {text!r}")
    return Literal(match["pred"], tuple(x.strip() for x in match["args"].split(",")),
                   match["not"] is not None)
