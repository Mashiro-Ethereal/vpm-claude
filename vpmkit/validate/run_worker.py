"""Check one candidate in one GPU environment and write a JSON result."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
import traceback
from typing import Any

import torch
from torch import Tensor

from ..candidate import Problem, load_candidate
from ..errors import CandidateOutputError, CandidateRuntimeError
from ..teacher import Teacher
from ..world import Snapshot, make_views


def exception_problem(exc: Exception, candidate_dir: Path, seed: int, step: int,
                      function: str, target: str, code: str | None = None) -> Problem:
    """Keep candidate frames from the exception chain, innermost frame last."""
    if code is None:
        code = "run.output" if isinstance(exc, CandidateOutputError) else "run.error"
    if isinstance(exc, (CandidateRuntimeError, CandidateOutputError)):
        function, target = exc.function, exc.target
    frames = []
    causes = []
    current: BaseException | None = exc
    while current is not None:
        causes.append(f"{type(current).__name__}: {current}")
        for frame in traceback.extract_tb(current.__traceback__):
            path = Path(frame.filename).resolve()
            if path.is_relative_to(candidate_dir):
                frames.append((f"{path.relative_to(candidate_dir)}:{frame.lineno}", frame.line))
        current = current.__cause__ or (
            current.__context__ if not current.__suppress_context__ else None)
    fallback = (function if isinstance(exc, (CandidateRuntimeError, CandidateOutputError))
                and "(" not in target else target)
    location = frames[-1][0] if frames else fallback
    message = ("; caused by ".join(causes)
               + f"; function={function}; instance={target}; seed={seed}, step={step}")
    if frames:
        message += "\n" + "\n".join(f"  {where}: {line}" for where, line in frames)
    return Problem(code, location, message)


def nonfinite_problem(value: Tensor, function: str, target: str,
                      seed: int, step: int) -> Problem | None:
    if torch.isfinite(value).all():
        return None
    return Problem("run.nonfinite", target,
                   f"Non-finite output: NaN or Inf; function={function}; "
                   f"instance={target}; seed={seed}, step={step}")


def progress_name(teacher: Teacher, k: int) -> str:
    stage = teacher.stage_names[k]
    function = teacher.candidate.progress.get(stage)
    return function.__name__ if function is not None else f"default progress of {stage}"


def check_first_state(teacher: Teacher, snapshot: Snapshot) -> list[Problem]:
    """Evaluate functions independently so one failure does not hide another."""
    problems = []
    world, views, objects = make_views(snapshot)
    margins = torch.zeros(snapshot.batch_size, len(teacher.instances), device=snapshot.device)
    unavailable = set()
    for column, literal in enumerate(teacher._instances):
        try:
            value = teacher._call(snapshot, teacher.candidate.predicates[literal.predicate],
                                  literal.instance_text, world, *(views[key] for key in literal.args))
            margins[:, column] = value
            problem = nonfinite_problem(value, literal.predicate, literal.instance_text, 0, 0)
            if problem is not None:
                problems.append(problem)
        except Exception as exc:
            unavailable.add(literal.instance)
            problems.append(exception_problem(exc, teacher.candidate.path, 0, 0,
                                              literal.predicate, literal.instance_text))
    scores = teacher._progress_scores(margins)
    for k, stage in enumerate(teacher.stage_names):
        if stage not in teacher.candidate.progress and any(
                literal.instance in unavailable for literal in teacher._guards[k]):
            continue  # A default cannot be evaluated without its guard's margins.
        name = progress_name(teacher, k)
        try:
            value = teacher._stage_progress(snapshot, k, scores, world, objects)
            problem = nonfinite_problem(value, name, name, 0, 0)
            if problem is not None:
                problems.append(problem)
        except Exception as exc:
            problems.append(exception_problem(exc, teacher.candidate.path, 0, 0, name, name))
    return problems


def check_state(teacher: Teacher, snapshot: Snapshot, seed: int, step: int) -> Problem | None:
    function = "compute_margins"
    try:
        margins = teacher.compute_margins(snapshot)
        function = "compute_progress"
        progress = teacher.compute_progress(snapshot, margins)
        for column, literal in enumerate(teacher._instances):
            problem = nonfinite_problem(margins[:, column], literal.predicate,
                                        literal.instance_text, seed, step)
            if problem is not None:
                return problem
        for k in range(teacher.num_stages):
            name = progress_name(teacher, k)
            problem = nonfinite_problem(progress[:, k], name, name, seed, step)
            if problem is not None:
                return problem
        function = "Teacher.step"
        teacher.step(snapshot)
    except Exception as exc:
        return exception_problem(exc, teacher.candidate.path, seed, step, function, function)
    return None


def run_candidate(candidate_dir: str | Path, env_id: str) -> dict[str, Any]:
    started = time.perf_counter()
    candidate_dir = Path(candidate_dir).resolve()
    problems: list[Problem] = []
    env = None
    states = 0
    seed = step = 0
    operation = "load_candidate"
    setup_seconds = 0.0
    rollout_started = None
    try:
        candidate = load_candidate(candidate_dir)
        from ..adapters.maniskill import ManiSkillAdapter, make_env

        operation = "make_env"
        env = make_env(env_id, num_envs=8)
        teacher = None
        adapter = None
        for seed in (0, 1, 2):
            step = 0
            operation = "env.reset"
            env.reset(seed=seed)
            env.action_space.seed(seed)
            for step in range(31):
                if step:
                    operation = "env.step"
                    env.step(env.action_space.sample())
                try:
                    if adapter is None:
                        adapter = ManiSkillAdapter(env, candidate.bind)
                    snapshot = adapter.snapshot()
                except Exception as exc:
                    problems.append(exception_problem(exc, candidate_dir, seed, step,
                                                      "bind/snapshot", "bind", "run.bind"))
                    break
                if teacher is None:
                    for i, official in enumerate(candidate.graph.official):
                        if official.key not in snapshot.official:
                            problems.append(Problem(
                                "run.official_key", f"stage_graph.yaml: official[{i}].key",
                                f"KeyError: evaluate() does not return {official.key!r}; "
                                f"function=evaluate; instance={official.literals}; seed={seed}, step={step}"))
                    operation = "Teacher"
                    teacher = Teacher(candidate, num_envs=8, device=env.unwrapped.device)
                    setup_seconds = time.perf_counter() - started
                    rollout_started = time.perf_counter()
                if step == 0:
                    teacher.reset()
                states += snapshot.batch_size
                if seed == 0 and step == 0:
                    problems.extend(check_first_state(teacher, snapshot))
                    if problems:
                        break
                problem = check_state(teacher, snapshot, seed, step)
                if problem is not None:
                    problems.append(problem)
                    break
            if problems:
                break
    except Exception as exc:
        problems.append(exception_problem(exc, candidate_dir, seed, step, operation, operation))
    finally:
        rollout_seconds = (time.perf_counter() - rollout_started
                           if rollout_started is not None else 0.0)
        if env is not None:
            try:
                env.close()
            except Exception as exc:
                problems.append(exception_problem(exc, candidate_dir, seed, step, "env.close", "env.close"))
    return {"problems": [asdict(problem) for problem in problems], "states": states,
            "timing": {"total_seconds": time.perf_counter() - started,
                       "setup_seconds": setup_seconds, "rollout_seconds": rollout_seconds}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--env", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = run_candidate(args.candidate, args.env)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
