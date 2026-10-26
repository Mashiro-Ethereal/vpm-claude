"""Render guard guidance on demand."""

from string import Formatter
from typing import TYPE_CHECKING

from torch import Tensor

if TYPE_CHECKING:
    from .teacher import Teacher


def render(teacher: "Teacher", output: dict[str, Tensor], i: int) -> list[str]:
    k = int(output["stage"][i])
    messages = []
    for literal in teacher._guards[k]:
        column = teacher._instance_columns[literal.instance]
        if not output["guidance"][i, column]:
            continue
        meta = teacher.candidate.predicates[literal.predicate].meta
        template = meta.need_false if literal.negated else meta.need_true
        if template is None:
            raise ValueError(f"{literal}: missing need_false template")
        names = {param: teacher.candidate.graph.objects[key].name
                 for param, key in zip(meta.object_params, literal.args)}
        for _, placeholder, spec, conversion in Formatter().parse(template):
            if placeholder is not None and (placeholder not in names or spec or conversion):
                raise ValueError(f"{literal}: unknown placeholder {{{placeholder}}}")
        text = template.format_map(names)
        messages.append(text[:1].upper() + text[1:])
    return messages
