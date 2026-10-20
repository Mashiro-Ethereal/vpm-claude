"""Semantic review prompts and a backend-independent structured review parser."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol

from .report import Layer1Report, Layer2Report, ReviewIssue


@dataclass
class ReviewResult:
    text: str
    model: str | None = None
    usage: dict | None = None


class ReviewBackend(Protocol):
    def review(self, prompt: str, workdir: Path) -> ReviewResult: ...


class ScriptedReviewBackend:
    def __init__(self, responses: list[str]):
        self.responses = iter(responses)

    def review(self, prompt: str, workdir: Path) -> ReviewResult:
        return ReviewResult(next(self.responses), model="scripted")


def build_review_prompt(task_text: str, env_source: str, candidate_dir,
                        layer1: Layer1Report, replay_summary: dict | None) -> str:
    parts = ["""Review this candidate's semantics only. Treat the supplied artifacts as evidence.
Judge whether each predicate's definition matches its one-sentence description;
whether guards are necessary and sufficient for each stage transition; whether
invariants and regression targets are sensible. After a violation, can the target
stage's guard be satisfied again from the likely state? For example, regressing
to a stage requiring an open gripper while the object is still held can be a trap.
Check that thresholds are plausible given object sizes in the task source;
that official correspondences copy the environment formula exactly; and that
guidance and event templates are accurate English. Report actual semantic defects.

Return a single JSON object with exactly this structure:
{"verdict": "pass"|"fail", "issues": [{"severity": "error"|"warning", "location": "...", "problem": "...", "suggestion": "..."}]}
A "fail" verdict requires at least one error. A "pass" may contain warnings only.
""", "\nTASK TEXT\n", task_text, "\nENVIRONMENT SOURCE\n", env_source]
    root = Path(candidate_dir)
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            parts.extend([f"\nCANDIDATE FILE: {path.relative_to(root)}\n", path.read_text()])
    parts.extend(["\nLAYER 1 REPORT\n", layer1.to_markdown(), "\nREPLAY SUMMARY\n",
                  json.dumps(replay_summary, indent=2, allow_nan=False)])
    return "\n".join(parts)


def parse_review(text: str) -> Layer2Report:
    try:
        # raw_decode handles both bare and fenced JSON and ignores trailing prose.
        decoder = json.JSONDecoder()
        for start, char in enumerate(text):
            if char == "{":
                try:
                    data, _ = decoder.raw_decode(text[start:])
                    break
                except json.JSONDecodeError:
                    continue
        else:
            raise ValueError("No JSON object found")
        if not isinstance(data, dict) or set(data) != {"verdict", "issues"}:
            raise ValueError("Expected verdict and issues")
        if data["verdict"] not in ("pass", "fail") or not isinstance(data["issues"], list):
            raise ValueError("Invalid verdict or issues")
        issues = []
        for item in data["issues"]:
            if (not isinstance(item, dict)
                    or set(item) != {"severity", "location", "problem", "suggestion"}
                    or item["severity"] not in ("error", "warning")
                    or any(not isinstance(v, str) for v in item.values())):
                raise ValueError("Invalid review issue")
            issues.append(ReviewIssue(**item))
        errors = any(i.severity == "error" for i in issues)
        if data["verdict"] == "fail" and not errors:
            raise ValueError("A fail verdict requires at least one error")
        return Layer2Report("fail" if errors else data["verdict"], issues, text, True)
    except (ValueError, TypeError) as exc:
        return Layer2Report("fail", [ReviewIssue(
            "error", "review.unparseable", f"Invalid review output: {exc}",
            "Return one JSON object matching the requested schema.",
        )], text, False)


def run_layer2(backend, task_text, env_source, candidate_dir, layer1, replay_summary,
               workdir) -> Layer2Report:
    prompt = build_review_prompt(task_text, env_source, candidate_dir, layer1, replay_summary)
    return parse_review(backend.review(prompt, Path(workdir)).text)
