"""Serializable validation reports."""

from dataclasses import asdict, dataclass, field
import json
from typing import Literal

from ..artifact.schema import Issue


@dataclass
class CheckResult:
    name: str
    status: Literal["pass", "fail", "warn", "skipped"]
    issues: list[Issue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.status not in {"pass", "fail", "warn", "skipped"}:
            raise ValueError(f"Invalid check status: {self.status!r}")


@dataclass
class Layer1Report:
    candidate_dir: str
    env_id: str
    passed: bool
    checks: list[CheckResult]
    replay_summary: dict | None
    started_at: str
    finished_at: str

    def __post_init__(self):
        self.candidate_dir = str(self.candidate_dir)
        self.passed = not any(check.status == "fail" for check in self.checks)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, allow_nan=False)

    @classmethod
    def from_json(cls, text: str) -> "Layer1Report":
        data = json.loads(text)
        data["checks"] = [CheckResult(**{**check, "issues": [Issue(**i) for i in check["issues"]]})
                          for check in data["checks"]]
        return cls(**data)

    def to_markdown(self) -> str:
        lines = ["# Layer 1 validation", "", f"Candidate: `{self.candidate_dir}`",
                 f"Environment: `{self.env_id}`", f"Result: {'PASS' if self.passed else 'FAIL'}",
                 f"Started: {self.started_at}", f"Finished: {self.finished_at}"]
        for check in self.checks:
            lines.extend(["", f"## {check.name}: {check.status}", ""])
            for issue in check.issues:
                lines.append(f"- `{issue.code}` at `{issue.where}`: {issue.message}")
            if check.stats:
                lines.extend(["", "```json", json.dumps(check.stats, indent=2, allow_nan=False), "```"])
        if self.replay_summary is not None:
            lines.extend(["", "## Replay summary", "", "```json",
                          json.dumps(self.replay_summary, indent=2, allow_nan=False), "```"])
        return "\n".join(lines) + "\n"


@dataclass
class ReviewIssue:
    severity: Literal["error", "warning"]
    location: str
    problem: str
    suggestion: str


@dataclass
class Layer2Report:
    verdict: Literal["pass", "fail"]
    issues: list[ReviewIssue]
    raw_text: str
    parse_ok: bool
