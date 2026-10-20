"""Ordered hard gates, with one fresh process per simulator validation."""

import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import traceback

import torch
import yaml

from ..artifact.loader import CandidateError, load_candidate
from ..artifact.schema import Issue
from ..artifact.astcheck import check_candidate_ast
from ..artifact.literals import parse_literal
from ..runtime.teacher import Teacher
from ..world import WorldState
from .replay import load_trajectories, save_trajectories, _summarize_replays
from .report import CheckResult, Layer1Report


CHECKS = ("parse", "schema", "ast", "run", "official", "trajectories")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _exception(code, where):
    return Issue(code, "\n".join(traceback.format_exc().splitlines()[-12:]), where)


def official_agreement(teacher, states, *, evaluations=None) -> CheckResult:
    """Compare declarations on individual rows; optional cached (margin, value) pairs."""
    issues, entries = [], []
    if evaluations is None:
        evaluations = [teacher.evaluate(state.to(teacher.device)) for state in states]
    indices = {key: i for i, key in enumerate(teacher.instance_keys)}
    failed = False
    for decl_id, decl in enumerate(teacher.candidate.graph.official):
        refs = [(text, parse_literal(text)) for text in decl.literals]
        conjunctions, officials, examples = [], [], []
        missing = False
        for state_id, (state, (margin, value)) in enumerate(zip(states, evaluations)):
            if decl.key not in state.official:
                issues.append(Issue("official.missing", f"evaluate() has no key {decl.key!r}",
                                    f"official[{decl_id}], state[{state_id}]"))
                missing = True
                continue
            off = state.official[decl.key].detach().cpu()
            if off.shape != (state.N,) or not torch.isfinite(off).all():
                issues.append(Issue("official.output", f"{decl.key!r} must be finite with shape [{state.N}]",
                                    f"official[{decl_id}], state[{state_id}]"))
                missing = True
                continue
            off = off.bool()
            value, margin = value.detach().cpu(), margin.detach().cpu()
            conj = torch.ones(state.N, dtype=torch.bool)
            for _, lit in refs:
                truth = value[:, indices[lit.instance_key]]
                conj &= truth if lit.positive else ~truth
            conjunctions.append(conj)
            officials.append(off)
            for row in (conj != off).nonzero().flatten().tolist()[:5 - len(examples)]:
                examples.append({"state": state_id, "row": row, "conjunction": bool(conj[row]),
                                 "official": bool(off[row]),
                                 "margins": {text: float(margin[row, indices[lit.instance_key]])
                                             for text, lit in refs}})
        conj = torch.cat(conjunctions) if conjunctions else torch.empty(0, dtype=torch.bool)
        off = torch.cat(officials) if officials else torch.empty(0, dtype=torch.bool)
        n = off.numel()
        agreement = float((conj == off).double().mean()) if n else None
        constant = n == 0 or bool((off == off[0]).all())
        mismatch = bool((conj != off).any())
        bad = missing or (mismatch if constant else agreement < 0.995)
        failed |= bad
        status = "fail" if bad else "warn" if constant else "pass"
        entries.append({"key": decl.key, "literals": decl.literals, "status": status,
                        "agreement": agreement, "conjunction_fraction_true": float(conj.double().mean()) if n else None,
                        "official_fraction_true": float(off.double().mean()) if n else None,
                        "num_states": n, "mismatches": examples})
        if bad and mismatch:
            issues.append(Issue("official.disagreement", f"{decl.key}: agreement={agreement:.6f}",
                                f"official[{decl_id}]"))
        elif constant and not missing:
            issues.append(Issue("official.uncovered", f"{decl.key}: official judgment is constant across {n} states",
                                f"official[{decl_id}]"))
    status = "fail" if failed else "warn" if issues else "pass"
    return CheckResult("official", status, issues, {"entries": entries})


def trajectory_checks(teacher, trajectories):
    """Gate successful demonstrations and summarize all supplied trajectories."""
    outputs = [teacher.run_sequence(t.states.to(teacher.device)) for t in trajectories]
    summary = _summarize_replays(teacher, trajectories, outputs)
    successful = [out for traj, out in zip(trajectories, outputs) if traj.success]
    issues = []
    if successful:
        values = torch.cat([out.value for out in successful])
        for stage_id, stage in enumerate(teacher.candidate.graph.stages):
            for text, (idx, positive) in zip(stage.exit, teacher.tables.exits[stage_id]):
                truth = values[:, idx] if positive else ~values[:, idx]
                if not truth.any() or truth.all():
                    issues.append(Issue("trajectory.constant_literal", f"{text} does not take both truth values",
                                        f"stages[{stage_id}].exit"))
    else:
        issues.append(Issue("trajectory.no_success", "No successful trajectories were supplied", "trajectories"))
    passed = sum(bool(out.done.any()) and not bool(out.regressed.any()) for out in successful)
    ratio = passed / len(successful) if successful else 0.0
    if ratio < 0.9:
        issues.append(Issue("trajectory.pass_through", f"{passed}/{len(successful)} successful trajectories reached done without regression; need 90%",
                            "trajectories"))
    return CheckResult("trajectories", "fail" if issues else "pass", issues,
                       {"num_trajectories": len(trajectories), "num_successful": len(successful),
                        "num_pass_through": passed, "pass_through_ratio": ratio}), summary


def _parse(candidate_dir):
    issues = []
    try:
        yaml.safe_load((candidate_dir / "stage_graph.yaml").read_text())
    except (OSError, yaml.YAMLError) as exc:
        issues.append(Issue("parse.yaml", str(exc), "stage_graph.yaml"))
    for filename in ("predicates.py", "progress.py", "bindings.py"):
        path = candidate_dir / filename
        if filename == "progress.py" and not path.exists():
            continue
        try:
            ast.parse(path.read_text(), filename=str(path))
        except (OSError, SyntaxError) as exc:
            issues.append(Issue("parse.python", str(exc), filename))
    return CheckResult("parse", "fail" if issues else "pass", issues)


def _run_frames(teacher, sequences):
    """Consume seed sequences online; retain snapshots and evaluated instances on CPU."""
    states, evaluations, outputs = [], [], []
    try:
        for frames in sequences:
            teacher.reset()
            for state in frames:
                out = teacher.step(state.to(teacher.device))
                for name, tensor in vars(out).items():
                    tail = (teacher.K,) if name == "progress_raw" else (
                        (teacher.I,) if name in {"margin", "value", "need_true", "need_false"} else ())
                    if tuple(tensor.shape) != (teacher.num_envs, *tail) or not torch.isfinite(tensor).all():
                        raise ValueError(f"Teacher.{name}: invalid shape or non-finite output")
                states.append(state.to("cpu"))
                evaluations.append((out.margin.detach().cpu(), out.value.detach().cpu()))
                outputs.append({key: tensor.detach().cpu() for key, tensor in vars(out).items()})
    except Exception:
        return CheckResult("run", "fail", [_exception("run.exception", "snapshot / Teacher.step (predicate, progress, automaton)")]), states, evaluations
    if not outputs:
        return CheckResult("run", "fail", [Issue("run.empty", "No states were evaluated", "run")]), states, evaluations
    values = torch.cat([o["value"] for o in outputs])
    stages = torch.cat([o["stage"] for o in outputs])
    names = [s.name for s in teacher.candidate.graph.stages] + ["done"]
    return CheckResult("run", "pass", stats={
        "num_states": len(stages),
        "instance_fraction_true": dict(zip(teacher.instance_keys, values.double().mean(0).tolist())),
        "stage_occupancy": {name: float((stages == i).double().mean()) for i, name in enumerate(names)},
        "num_regressions": sum(int(o["regressed"].sum()) for o in outputs),
        "guidance_fraction": sum(int((o["need_true"] | o["need_false"]).any(1).sum()) for o in outputs) / len(stages),
    }), states, evaluations


def _validate(candidate_dir, env_id, num_envs, seeds, steps, trajectories, extra_states, device):
    started = _now()
    checks, summary = [], None

    def finish():
        checks.extend(CheckResult(name, "skipped") for name in CHECKS[len(checks):])
        return Layer1Report(str(candidate_dir), env_id, True, checks, summary, started, _now())

    checks.append(_parse(candidate_dir))
    if checks[-1].status == "fail":
        return finish()
    try:
        candidate = load_candidate(candidate_dir, check_ast=False)
        checks.append(CheckResult("schema", "pass"))
    except CandidateError as exc:
        checks.append(CheckResult("schema", "fail", exc.issues))
        return finish()
    except Exception:
        checks.append(CheckResult("schema", "fail", [_exception("schema.load", "load_candidate")]))
        return finish()
    issues = check_candidate_ast(candidate_dir)
    checks.append(CheckResult("ast", "fail" if issues else "pass", issues))
    if issues:
        return finish()

    from ..adapters.maniskill import ManiSkillAdapter, make_env
    env, teacher = None, None
    component = "make_env"
    try:
        env = make_env(env_id, num_envs)
        component = "bindings.py:bind / ManiSkillAdapter"
        adapter = ManiSkillAdapter(env, candidate.bind)
        component = "Teacher initialization"
        teacher = Teacher(candidate, num_envs, device=device or adapter.device)

        def frames(seed):
            env.reset(seed=seed)
            env.action_space.seed(seed)
            yield adapter.snapshot()
            for _ in range(steps):
                env.step(env.action_space.sample())
                yield adapter.snapshot()

        run, states, evaluations = _run_frames(teacher, (frames(seed) for seed in seeds))
        checks.append(run)
    except Exception:
        checks.append(CheckResult("run", "fail", [_exception("run.exception", component)]))
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                checks[-1].status = "fail"
                checks[-1].issues.append(_exception("run.close", "env.close"))
    if checks[-1].status == "fail":
        return finish()
    try:
        additional = [t.states for t in trajectories or []] + list(extra_states or [])
        evaluations.extend(teacher.evaluate(state.to(teacher.device)) for state in additional)
        checks.append(official_agreement(teacher, states + additional, evaluations=evaluations))
    except Exception:
        checks.append(CheckResult("official", "fail", [_exception("official.exception", "official states / predicates")]))
    if trajectories is not None:
        try:
            result, summary = trajectory_checks(teacher, trajectories)
            checks.append(result)
        except Exception:
            checks.append(CheckResult("trajectories", "fail", [_exception("trajectory.exception", "Teacher.run_sequence")]))
    return finish()


def validate_layer1(candidate_dir, env_id, *, num_envs=8, seeds=(0, 1, 2), steps=30,
                    trajectories=None, extra_states=None, device=None, isolate=True) -> Layer1Report:
    """Validate in a fresh subprocess by default; device selects Teacher evaluation.

    The simulator backend follows make_env: CPU for N=1, CUDA for larger batches.
    """
    candidate_dir = Path(candidate_dir).resolve()
    if num_envs < 1 or steps < 0 or not seeds:
        raise ValueError("Require num_envs >= 1, steps >= 0, and at least one seed")
    if not isolate:
        return _validate(candidate_dir, env_id, num_envs, seeds, steps, trajectories, extra_states, device)
    started = _now()
    with tempfile.TemporaryDirectory(prefix="vpm-validate-") as temp:
        temp = Path(temp)
        config = {"candidate_dir": str(candidate_dir), "env_id": env_id, "num_envs": num_envs,
                  "seeds": list(seeds), "steps": steps, "device": str(device) if device is not None else None}
        if trajectories is not None:
            save_trajectories(temp / "trajectories.pt", trajectories)
            config["trajectories_path"] = str(temp / "trajectories.pt")
        if extra_states is not None:
            torch.save([state.to("cpu").to_dict() for state in extra_states], temp / "extra.pt")
            config["extra_states_path"] = str(temp / "extra.pt")
        (temp / "config.json").write_text(json.dumps(config))
        root = Path(__file__).resolve().parents[2]
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "0"),
               "PYTHONDONTWRITEBYTECODE": "1",
               "XDG_CACHE_HOME": str(root / "outputs/cache")}
        result = subprocess.run([sys.executable, "-m", "vpmkit.validate.layer1",
                                 "--config", str(temp / "config.json"), "--json-out", str(temp / "report.json")],
                                cwd=root, env=env, capture_output=True, text=True)
        if result.returncode == 0 and (temp / "report.json").exists():
            return Layer1Report.from_json((temp / "report.json").read_text())
        checks = [CheckResult(name, "skipped") for name in CHECKS]
        checks[3] = CheckResult("run", "fail", [Issue(
            "run.subprocess", f"Validation subprocess exited {result.returncode}\n" +
            "\n".join((result.stdout + result.stderr).splitlines()[-12:]), "subprocess",
        )])
        return Layer1Report(str(candidate_dir), env_id, False, checks, None, started, _now())


def _main():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    trajectories_path = config.pop("trajectories_path", None)
    extra_path = config.pop("extra_states_path", None)
    if trajectories_path:
        config["trajectories"] = load_trajectories(trajectories_path)
    if extra_path:
        config["extra_states"] = [WorldState.from_dict(state) for state in
                                  torch.load(extra_path, map_location="cpu", weights_only=True)]
    report = validate_layer1(**config, isolate=False)
    Path(args.json_out).write_text(report.to_json())


if __name__ == "__main__":
    _main()
