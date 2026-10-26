"""Render task helper descriptions from the ManiSkill helper table."""

import textwrap

from ..adapters.maniskill.helpers_table import HELPERS, TASK_HELPERS


HEADER = "# Helpers that evaluate() in env_source.py calls, and how a candidate uses each."
SEPARATOR = "# ---------------------------------------------------------------------------"


def render_helpers_py(env_id: str) -> str:
    entries = TASK_HELPERS.get(env_id, [])
    if not entries:
        return HEADER + "\n# evaluate() calls no helper outside the task class.\n"
    blocks = [HEADER]
    for helper_id, call in entries:
        helper = HELPERS[helper_id]
        lines = [SEPARATOR, f"# {call}", f"#   {helper.defined_at}"]
        lines.extend(textwrap.wrap(helper.candidate_use, width=79,
                                   initial_indent="#   ", subsequent_indent="#   ",
                                   break_long_words=False, break_on_hyphens=False))
        if helper.source_included:
            lines.append(helper.source().rstrip("\n"))
        else:
            lines.append("#   Source not included.")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"
