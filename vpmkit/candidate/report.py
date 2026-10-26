"""Serializable, actionable candidate check results."""

from dataclasses import asdict, dataclass
import json

from .codes import CODES


GROUPS = ("parse", "schema", "ast", "run")


@dataclass(frozen=True)
class Problem:
    code: str
    location: str
    message: str

    def __post_init__(self) -> None:
        if self.code not in CODES:
            raise ValueError(f"Unknown check code: {self.code}")


@dataclass
class Report:
    candidate: str
    groups: dict[str, str]
    problems: list[Problem]

    def __post_init__(self) -> None:
        if set(self.groups) != set(GROUPS):
            raise ValueError(f"Report groups must be {GROUPS}")
        if any(status not in {"passed", "failed", "skipped"} for status in self.groups.values()):
            raise ValueError("Group status must be passed, failed or skipped")

    @property
    def passed(self) -> bool:
        return ("failed" not in self.groups.values()
                and all(self.groups[group] == "passed" for group in GROUPS[:3]))

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "Report":
        data = json.loads(text)
        return cls(candidate=data["candidate"], groups=data["groups"],
                   problems=[Problem(**problem) for problem in data["problems"]])

    def to_markdown(self) -> str:
        lines = [f"Check report: {'PASSED' if self.passed else 'FAILED'}", "",
                 *(f"- {group}: {self.groups[group]}" for group in GROUPS)]
        if self.problems:
            lines.append("")
            lines.extend(f"{i}. `{p.code}` at {p.location}: {p.message}"
                         for i, p in enumerate(self.problems, 1))
        return "\n".join(lines) + "\n"
