"""Run generation rounds, retry harness failures and preserve each attempt."""

from collections import Counter
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import shutil
from typing import Any, Literal

from ..validate import REPO_ROOT
from ..validate.layer1 import run_layer1
from .backends import Backend, ReviewCall, RoundResult
from .env import child_env, env_names
from .review import ReviewItem, ReviewParseError, parse_review, render_review, review_prompt
from .rundir import Run, create_run


@dataclass
class Verdict:
    status: Literal["passed", "failed", "harness_failure"]
    run_dir: Path
    rounds: list[dict[str, Any]]
    error: str | None = None

    @property
    def rounds_used(self) -> int:
        return len(self.rounds)

    def to_json(self) -> str:
        return json.dumps({"status": self.status, "rounds_used": self.rounds_used,
                           "rounds": self.rounds, "error": self.error}, indent=2) + "\n"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _repair_prompt(round_number: int, report: str, review: bool = False) -> str:
    prompt = (f"The checks after round {round_number} found problems in candidate/. "
              "Fix them, run ./check.sh until it passes, and end your turn with a short summary.")
    if review:
        prompt += ("\n\nIf you disagree with an error, do not change the candidate for it; "
                   "give your reasons under the heading Responses to review at the end of candidate/notes.md.")
    return prompt + "\n\n" + report


def _attempt_dir(round_dir: Path, step: str, attempt: int) -> Path:
    directory = round_dir if attempt == 0 else round_dir / f"{step}_retry_{attempt}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _call_error(directory: Path, name: str, exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}"
    (directory / f"{name}.jsonl").touch(exist_ok=True)
    with (directory / f"{name}.stderr.txt").open("a", encoding="utf-8") as stream:
        stream.write(message + "\n")
    return message


def run_generation(env_id: str, backend: Backend, config: dict[str, Any],
                   run: Run | None = None) -> Verdict:
    config = deepcopy(config)
    if config["max_rounds"] < 1 or config["harness_retries"] < 0:
        raise ValueError("max_rounds must be positive and harness_retries must be nonnegative")
    if run is None:
        run = create_run(REPO_ROOT / config["paths"]["packages"] / env_id,
                         REPO_ROOT / config["paths"]["runs"], env_id, config["gpu"])
    elif run.env_id != env_id:
        raise ValueError("Run environment does not match env_id")
    backend.gpu = run.gpu
    config["gpu"] = run.gpu
    manifest = json.loads((run.workspace / "manifest.json").read_text(encoding="utf-8"))
    metadata = {
        "env_id": env_id, "package_sha256": manifest["package_sha256"], "config": config,
        "environment_names": env_names(child_env(run.gpu)), "backend": type(backend).__name__,
        "cli_version": None, "session_id": None, "started_at": _now(), "ended_at": None,
    }
    _write_json(run.records / "run.json", metadata)
    verdict = Verdict("failed", run.path, [])
    session_id = None
    prompt = "Read TASK.md first."
    previous_items: list[ReviewItem] = []
    try:
        metadata["cli_version"] = backend.version()
        _write_json(run.records / "run.json", metadata)
        for number in range(1, config["max_rounds"] + 1):
            directory = run.records / f"round_{number}"
            directory.mkdir()
            summary: dict[str, Any] = {
                "round": number, "generation_attempts": [], "review_attempts": [],
                "layer1_codes": {}, "review_error_categories": {}, "check_sh_calls": 0,
            }
            verdict.rounds.append(summary)
            for attempt in range(config["harness_retries"] + 1):
                attempt_dir = _attempt_dir(directory, "generation", attempt)
                (attempt_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
                try:
                    generated = backend.generate(run.workspace, prompt, session_id, record_dir=attempt_dir)
                except Exception as exc:
                    generated = RoundResult("error", error=_call_error(attempt_dir, "generation", exc))
                session_id = generated.session_id or session_id
                metadata["session_id"] = session_id
                _write_json(run.records / "run.json", metadata)
                _write_json(attempt_dir / "generation_result.json", asdict(generated))
                summary["generation_attempts"].append({
                    "record_dir": str(attempt_dir.relative_to(directory)), "outcome": generated.outcome})
                summary["check_sh_calls"] += generated.check_sh_calls
                if generated.outcome != "error":
                    break
            summary["generation_outcome"] = generated.outcome
            shutil.copytree(run.workspace / "candidate", directory / "candidate")
            if generated.outcome == "error":
                verdict.status = "harness_failure"
                verdict.error = generated.error or "Generation failed after all attempts"
                break

            report = run_layer1(run.workspace / "candidate", env_id)
            markdown = report.to_markdown()
            (directory / "layer1.json").write_text(report.to_json() + "\n", encoding="utf-8")
            (directory / "layer1.md").write_text(markdown, encoding="utf-8")
            summary["layer1_codes"] = dict(Counter(problem.code for problem in report.problems))
            summary["layer1_passed"] = report.layer1_passed
            if not report.layer1_passed:
                prompt = _repair_prompt(number, markdown)
                continue

            reviewer_prompt = review_prompt(env_id, markdown, previous_items)
            items = None
            for attempt in range(config["harness_retries"] + 1):
                attempt_dir = _attempt_dir(directory, "review", attempt)
                (attempt_dir / "review_prompt.txt").write_text(reviewer_prompt, encoding="utf-8")
                try:
                    reviewed = backend.review(run.workspace, reviewer_prompt, record_dir=attempt_dir)
                except Exception as exc:
                    reviewed = ReviewCall("error", error=_call_error(attempt_dir, "review", exc))
                _write_json(attempt_dir / "review_call.json", asdict(reviewed))
                review_error = reviewed.error
                if reviewed.succeeded:
                    try:
                        items = parse_review(reviewed.final_text)
                    except ReviewParseError as exc:
                        review_error = str(exc)
                else:
                    review_error = review_error or f"Review call ended with {reviewed.outcome}"
                summary["review_attempts"].append({
                    "record_dir": str(attempt_dir.relative_to(directory)),
                    "outcome": reviewed.outcome, "error": review_error})
                if items is not None:
                    break
            if items is None:
                verdict.status = "harness_failure"
                verdict.error = review_error
                break
            _write_json(directory / "review.json", [asdict(item) for item in items])
            rendered = render_review(items)
            (directory / "review.md").write_text(rendered, encoding="utf-8")
            summary["review_error_categories"] = dict(Counter(
                item.category for item in items if item.severity == "error"))
            if not summary["review_error_categories"]:
                verdict.status = "passed"
                break
            previous_items = items
            prompt = _repair_prompt(number, rendered, review=True)
    except Exception as exc:
        verdict.status = "harness_failure"
        verdict.error = f"{type(exc).__name__}: {exc}"
    finally:
        metadata["ended_at"] = _now()
        _write_json(run.records / "run.json", metadata)
        for summary in verdict.rounds:
            _write_json(run.records / f"round_{summary['round']}" / "round.json", summary)
        (run.records / "verdict.json").write_text(verdict.to_json(), encoding="utf-8")
    return verdict
