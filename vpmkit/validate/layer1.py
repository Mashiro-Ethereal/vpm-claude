"""Static checks followed by an isolated GPU run check."""

import json
from pathlib import Path
import resource
import subprocess
import tempfile
import time

from ..candidate import Problem, Report, check_static
from . import REPO_ROOT, VPM_PYTHON


def _disable_core_dumps() -> None:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _worker_error(message: str, stderr: str | bytes | None) -> Problem:
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    return Problem("run.error", "run_worker",
                   f"{message}\nWorker stderr (tail):\n{(stderr or '').strip()[-4000:]}")


def run_layer1(candidate_dir: str | Path, env_id: str, timeout: float = 900) -> Report:
    started = time.perf_counter()
    report = check_static(candidate_dir)
    report.timing["static_seconds"] = time.perf_counter() - started
    if report.passed:
        tmp = REPO_ROOT / "outputs/tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="check-", dir=tmp) as folder:
            output = Path(folder) / "run.json"
            command = [str(VPM_PYTHON), "-m", "vpmkit.validate.run_worker",
                       "--candidate", str(Path(candidate_dir).resolve()), "--env", env_id,
                       "--out", str(output)]
            worker_started = time.perf_counter()
            try:
                result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True,
                                        timeout=timeout, preexec_fn=_disable_core_dumps)
            except subprocess.TimeoutExpired as exc:
                report.problems.append(_worker_error(f"Worker timed out after {timeout:g} s", exc.stderr))
            else:
                if result.returncode:
                    report.problems.append(_worker_error(
                        f"Worker exited with code {result.returncode}", result.stderr))
                else:
                    try:
                        data = json.loads(output.read_text(encoding="utf-8"))
                        problems = [Problem(**problem) for problem in data["problems"]]
                        timing = {f"run_{key}": float(value) for key, value in data["timing"].items()}
                    except (OSError, ValueError, KeyError, TypeError) as exc:
                        report.problems.append(_worker_error(
                            f"Invalid worker result: {type(exc).__name__}: {exc}", result.stderr))
                    else:
                        report.problems.extend(problems)
                        report.timing.update(timing)
            report.timing["worker_seconds"] = time.perf_counter() - worker_started
        report.groups["run"] = "failed" if report.problems else "passed"
    report.timing["total_seconds"] = time.perf_counter() - started
    return report
