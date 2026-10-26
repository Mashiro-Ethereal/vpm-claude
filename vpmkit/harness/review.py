"""Review prompts, structured findings and repair reports."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re


CATEGORIES = {
    "a": "official", "b": "description", "c": "reachability", "d": "regress",
    "e": "blocking", "f": "granularity", "g": "templates", "h": "progress",
    "i": "thresholds", "j": "alternatives",
}
TEMPLATE = Path(__file__).resolve().parents[1] / "resources/review_prompt.md"


class ReviewParseError(ValueError):
    """The reviewer did not return the required JSON findings."""


@dataclass(frozen=True)
class ReviewItem:
    category: str
    severity: str
    location: str
    problem: str
    fix: str
    note: str = ""


def review_prompt(env_id: str, layer1_markdown: str,
                  previous_items: list[ReviewItem]) -> str:
    errors = [asdict(item) for item in previous_items if item.severity == "error"]
    previous = ("The previous review reported these errors:\n"
                + json.dumps(errors, indent=2, ensure_ascii=False)) if errors else ""
    replacements = {"env_id": env_id, "layer1_report": layer1_markdown,
                    "previous_review": previous}
    return re.sub(r"\{(env_id|layer1_report|previous_review)\}",
                  lambda match: replacements[match.group(1)], TEMPLATE.read_text(encoding="utf-8"))


def parse_review(text: str) -> list[ReviewItem]:
    text = text.strip()
    candidates = [text]
    candidates.extend(match.group(1) for match in re.finditer(
        r"```json\s*\n(.*?)\n```", text, flags=re.DOTALL))
    first, last = text.find("["), text.rfind("]")
    if 0 <= first < last:
        candidates.append(text[first:last + 1])
    error: ReviewParseError
    for candidate in candidates:
        try:
            return _parse_review_array(candidate)
        except ReviewParseError as exc:
            error = exc
    raise error


def _parse_review_array(text: str) -> list[ReviewItem]:
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ReviewParseError(f"Invalid review JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ReviewParseError("Review must be a JSON array")
    fields = ("category", "severity", "location", "problem", "fix")
    items = []
    for index, entry in enumerate(data):
        if not isinstance(entry, dict) or any(not isinstance(entry.get(key), str) for key in fields):
            raise ReviewParseError(f"Review item {index + 1} needs string fields: {', '.join(fields)}")
        if entry["category"] not in CATEGORIES or entry["severity"] not in {"error", "reminder"}:
            raise ReviewParseError(f"Review item {index + 1} has an invalid category or severity")
        values = {key: entry[key] for key in fields}
        if values["category"] in "fghij" and values["severity"] == "error":
            values["severity"] = "reminder"
            values["note"] = "Severity corrected from error to reminder for category " + values["category"]
        items.append(ReviewItem(**values))
    return items


def render_review(items: list[ReviewItem]) -> str:
    lines = ["Review report", ""]
    for severity, heading in (("error", "Errors"), ("reminder", "Reminders")):
        lines.extend([f"## {heading}", ""])
        selected = [item for item in items if item.severity == severity]
        if not selected:
            lines.extend(["None.", ""])
        for item in selected:
            lines.extend([f"- **{item.category}. {CATEGORIES[item.category]}** at {item.location}",
                          f"  Problem: {item.problem}", f"  Suggested fix: {item.fix}"])
            if item.note:
                lines.append(f"  Note: {item.note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
