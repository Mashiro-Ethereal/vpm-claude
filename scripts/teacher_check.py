#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
"""Observe Stage1 PickCube teachers on first episodes of a trained PPO policy."""

import argparse
from datetime import datetime
from importlib.metadata import version
import json
import os
from pathlib import Path
import random
import shlex
import subprocess
import sys
import time
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import gymnasium as gym
import numpy as np
import torch
from torch import Tensor

# This import also sets the three ManiSkill cache directories under outputs/.
from scripts.ppo_check import Agent
from vpmkit.candidate import Candidate, load_candidate
from vpmkit.candidate.schema import StageGraph
from vpmkit.literal import parse_literal
from vpmkit.teacher import Teacher

POLICY = REPO_ROOT / "outputs/stage1/ppo_check/PickCube-v1-dense-seed1-20261026-202427/final_model.pt"
CANDIDATES = {
    "generated": REPO_ROOT / "outputs/stage1/runs/PickCube-v1/20261026-184803/records/round_1/candidate",
    "reference": REPO_ROOT / "candidates/reference/PickCube-v1",
}
OFFICIAL = ("success", "is_grasped", "is_obj_placed", "is_robot_static")
EPS = 1e-4


class TeacherObserver(gym.Wrapper):
    """Read both teachers before vector auto-reset, preserving the environment reward."""

    def __init__(self, env: gym.Env, candidates: dict[str, Candidate]) -> None:
        super().__init__(env)
        from vpmkit.adapters.maniskill import ManiSkillAdapter

        self.num_envs = env.unwrapped.num_envs
        self.device = env.unwrapped.device
        self.adapters = {label: ManiSkillAdapter(env, c.bind) for label, c in candidates.items()}
        self.teachers = {label: Teacher(c, self.num_envs, self.device) for label, c in candidates.items()}

    def observe(self, info: dict, env_mask: Tensor | None = None) -> dict:
        outputs = {}
        for label, teacher in self.teachers.items():
            out = teacher.step(self.adapters[label].snapshot(info), env_mask=env_mask)
            outputs[label] = {key: value.detach().clone() for key, value in out.items()}
        base = self.env.unwrapped
        tcp, cube, goal = base.agent.tcp.pose.p, base.cube.pose.p, base.goal_site.pose.p
        outputs["geom"] = {
            "tcp_cube_dist": torch.linalg.vector_norm(tcp - cube, dim=-1).clone(),
            "cube_goal_dist": torch.linalg.vector_norm(cube - goal, dim=-1).clone(),
            "cube_z": cube[:, 2].clone(),
        }
        info["teacher_check"] = outputs
        return info

    def reset(self, *, seed: int | list[int] | None = None,
              options: dict[str, Any] | None = None) -> tuple[Any, dict]:
        obs, info = self.env.reset(seed=seed, options=options)
        env_idx = options.get("env_idx") if options is not None else None
        env_mask = None
        if env_idx is not None:
            env_mask = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
            env_mask[env_idx] = True
        for teacher in self.teachers.values():
            teacher.reset(env_idx=env_idx)
        return obs, self.observe(info, env_mask)

    def step(self, action: Any) -> tuple:
        obs, reward, terminated, truncated, info = self.env.step(action)
        return obs, reward, terminated, truncated, self.observe(info)


def tree_map(function, tree: dict) -> dict:
    return {key: tree_map(function, value) if isinstance(value, dict) else function(value)
            for key, value in tree.items()}


def concatenate_rollouts(batches: list[dict]) -> dict:
    return {key: concatenate_rollouts([batch[key] for batch in batches])
            if isinstance(batches[0][key], dict) else torch.cat([batch[key] for batch in batches])
            for key in batches[0]}


@torch.no_grad()
def rollout(agent: Agent, envs: Any, seed: int, deterministic: bool,
            max_steps: int = 50) -> dict:
    """Record [episode, time, ...] tensors, zero-padding after the first episode."""
    obs, info = envs.reset(seed=seed)
    count, device = envs.num_envs, envs.device
    initial = info["teacher_check"]
    recorded = {}
    for label, output in initial.items():
        recorded[label] = {}
        for key, value in output.items():
            dtype = torch.int8 if key == "stage" else value.dtype
            recorded[label][key] = torch.zeros(
                (count, max_steps + 1, *value.shape[1:]), dtype=dtype, device=device)
            recorded[label][key][:, 0] = value
    data = {
        "teachers": {key: value for key, value in recorded.items() if key != "geom"},
        "geom": recorded["geom"],
        "official": {key: torch.zeros(count, max_steps + 1, dtype=torch.bool, device=device)
                     for key in OFFICIAL},
        "mask": torch.zeros(count, max_steps + 1, dtype=torch.bool, device=device),
        "official_mask": torch.zeros(count, max_steps + 1, dtype=torch.bool, device=device),
        "lengths": torch.zeros(count, dtype=torch.uint8, device=device),
        "seed": torch.full((count,), seed, dtype=torch.int32, device=device),
        "env_index": torch.arange(count, dtype=torch.int32, device=device),
        "terminated": torch.zeros(count, dtype=torch.bool, device=device),
        "truncated": torch.zeros(count, dtype=torch.bool, device=device),
    }
    data["mask"][:, 0] = True
    active = torch.ones(count, dtype=torch.bool, device=device)
    low = torch.as_tensor(envs.single_action_space.low, device=device)
    high = torch.as_tensor(envs.single_action_space.high, device=device)
    for t in range(1, max_steps + 1):
        action = agent.get_action(obs, deterministic=deterministic).clamp(low, high)
        obs, _, terminated, truncated, info = envs.step(action)
        step_info = info.get("final_info", info)
        for label, output in step_info["teacher_check"].items():
            for key, value in output.items():
                recorded[label][key][active, t] = value[active].to(recorded[label][key].dtype)
        for key in OFFICIAL:
            data["official"][key][active, t] = step_info[key][active].bool()
        data["mask"][active, t] = True
        data["official_mask"][active, t] = True
        data["lengths"][active] += 1
        ended = active & (terminated | truncated)
        data["terminated"][ended] = terminated[ended]
        data["truncated"][ended] = truncated[ended]
        active &= ~ended
        if not active.any():
            break
    if active.any():
        raise RuntimeError("Rollout ended before every first episode finished")
    return tree_map(lambda value: value.cpu(), data)


def describe(values: Tensor, quantiles: bool = False) -> dict:
    values = values.double().flatten()
    result = {"count": values.numel(), "mean": None, "min": None, "max": None}
    if values.numel():
        result.update(mean=values.mean().item(), min=values.min().item(), max=values.max().item())
    if quantiles:
        for key, q in (("median", 0.5), ("p10", 0.1), ("p90", 0.9)):
            result[key] = torch.quantile(values, q).item() if values.numel() else None
    return result


def fraction(numerator: Tensor, denominator: Tensor) -> float | None:
    count = int(denominator.sum())
    return int((numerator & denominator).sum()) / count if count else None


def histogram(values: Tensor, names: list[str]) -> dict[str, int]:
    return dict(zip(names, torch.bincount(values.long(), minlength=len(names)).tolist()))


def spearman(x: Tensor, y: Tensor) -> float | None:
    """Pearson correlation of average ranks; constant inputs have no correlation."""
    def ranks(value: Tensor) -> np.ndarray:
        _, inverse, counts = np.unique(value.double().numpy(), return_inverse=True, return_counts=True)
        return (np.cumsum(counts) - (counts - 1) / 2)[inverse]

    if x.numel() < 2:
        return None
    rx, ry = ranks(x), ranks(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    norm = np.linalg.norm(rx) * np.linalg.norm(ry)
    return float(np.dot(rx, ry) / norm) if norm else None


def literal_truth(text: str, instances: list[str], pred: Tensor) -> Tensor:
    literal = parse_literal(text)
    truth = pred[..., instances.index(literal.instance_text)]
    return ~truth if literal.negated else truth


def episode_classes(data: dict, goal_thresh: float) -> dict[str, Tensor]:
    success = (data["official"]["success"] & data["official_mask"]).any(1)
    trivial = success & (data["geom"]["cube_goal_dist"][:, 0] <= goal_thresh)
    return {"success": success, "non_trivial_success": success & ~trivial,
            "trivial_success": trivial, "failure": ~success}


def first_entries(condition: Tensor, mask: Tensor) -> tuple[Tensor, Tensor]:
    valid = condition & mask
    return valid.any(1), valid.int().argmax(1)


def official_correspondence(data: dict, output: dict, graph: StageGraph,
                            instances: list[str]) -> dict:
    results = {}
    mask = data["official_mask"]
    for official in graph.official:
        truths = [literal_truth(text, instances, output["pred"]) for text in official.literals]
        conjunction = torch.stack(truths).all(0)
        mismatch = mask & (conjunction != data["official"][official.key])
        examples = []
        for episode, t in mismatch.nonzero()[:5].tolist():
            examples.append({
                "episode": episode, "seed": int(data["seed"][episode]),
                "env_index": int(data["env_index"][episode]), "t": t,
                "environment": bool(data["official"][official.key][episode, t]),
                "conjunction": bool(conjunction[episode, t]),
                "literal_truth": {text: bool(truth[episode, t])
                                  for text, truth in zip(official.literals, truths)},
                "margins": {parse_literal(text).instance_text: float(output["margin"][
                    episode, t, instances.index(parse_literal(text).instance_text)])
                    for text in official.literals},
            })
        results[official.key] = {
            "literals": official.literals, "steps": int(mask.sum()),
            "agreement_rate": fraction(~mismatch, mask), "mismatch_count": int(mismatch.sum()),
            "examples": examples,
        }
    return results


def candidate_statistics(data: dict, label: str, graph: StageGraph,
                         instances: list[str], goal_thresh: float = 0.025) -> dict:
    """Compute sections a-f from recorded CPU tensors without changing teacher state."""
    output = data["teachers"][label]
    stage, phi = output["stage"].long(), output["phi"]
    names = [item.name for item in graph.stages]
    classes = episode_classes(data, goal_thresh)
    selected = classes["non_trivial_success"]
    mask, steps = data["mask"], data["official_mask"]
    transition_mask = mask[:, 1:] & mask[:, :-1]
    regress = (stage[:, 1:] < stage[:, :-1]) & transition_mask
    has_regression = regress.any(1)
    rows = torch.arange(stage.shape[0])
    lengths = data["lengths"].long()
    end_stage, end_phi = stage[rows, lengths], phi[rows, lengths]
    completed = (end_stage == len(names) - 1) & (end_phi == 1)
    chain = {
        "episodes": int(selected.sum()),
        "success_stage_histogram": histogram(end_stage[selected], names),
        "completed_fraction": fraction(completed, selected),
        "no_regression_fraction": fraction(~has_regression, selected),
        "chain_coverage": fraction(completed & ~has_regression, selected),
    }
    pairs = {}
    for source, target in torch.stack((stage[:, :-1][regress], stage[:, 1:][regress]), 1).unique(dim=0).tolist():
        pair = regress & (stage[:, :-1] == source) & (stage[:, 1:] == target)
        invariants = []
        any_false = torch.zeros_like(pair)
        for invariant in graph.stages[source].invariants:
            false = ~literal_truth(invariant.literal, instances, output["pred"][:, 1:])
            any_false |= false
            invariants.append({"literal": invariant.literal, "regress_to": invariant.regress_to,
                               "false_count": int((pair & false).sum())})
        pairs[f"{names[source]} -> {names[target]}"] = {
            "count": int(pair.sum()), "invariants": invariants,
            "no_false_invariant_count": int((pair & ~any_false).sum()),
        }
    regressions = {
        "total": int(regress.sum()), "per_episode": describe(regress.sum(1), True),
        "per_episode_histogram": {str(k): v for k, v in enumerate(torch.bincount(regress.sum(1)).tolist())},
        "pairs": pairs,
        "episodes_with_regression": {key: int((value & has_regression).sum())
                                     for key, value in classes.items() if key != "success"},
    }
    timing = {"initial_stage_histogram": histogram(stage[selected, 0], names), "stages": {}}
    for k, name in enumerate(names):
        reached, entry = first_entries(stage >= k, mask)
        dwell = ((stage == k) & mask).sum(1)
        skipped = (dwell == 0) & ((stage > k) & mask).any(1)
        timing["stages"][name] = {
            "first_entry": describe(entry[selected & reached], True),
            "dwell": describe(dwell[selected], True),
            "skipped_fraction": fraction(skipped, selected),
        }
    geometry = {}
    for key, condition, valid, field in (
        ("tcp_cube_at_grasp_entry", stage >= names.index("grasp"), mask, "tcp_cube_dist"),
        ("tcp_cube_at_first_grasped", data["official"]["is_grasped"], steps, "tcp_cube_dist"),
        ("cube_goal_at_carry_entry", stage >= names.index("carry"), mask, "cube_goal_dist"),
    ):
        reached, entry = first_entries(condition, valid)
        geometry[key] = describe(data["geom"][field][rows, entry][selected & reached], True)
    timing["entry_geometry_m"] = geometry
    delta = phi[:, 1:] - phi[:, :-1]
    valid_delta = transition_mask & selected[:, None]
    negative = delta < -EPS
    same_stage = stage[:, 1:] == stage[:, :-1]
    plateau = delta.abs() <= EPS
    negative_mass = torch.where(transition_mask, (-delta).clamp_min(0), 0).sum(1)
    negative_rates = {}
    plateaus = {}
    for k, name in enumerate(names):
        eligible = valid_delta & (stage[:, 1:] == k)
        negative_rates[name] = {
            "steps": int(eligible.sum()), "negative_count": int((negative & eligible).sum()),
            "fraction": fraction(negative, eligible),
            "stage_decrease_fraction": fraction(negative & regress, eligible),
            "same_stage_fraction": fraction(negative & same_stage, eligible),
        }
        plateaus[name] = {"steps": int(eligible.sum()), "count": int((plateau & eligible).sum()),
                          "fraction": fraction(plateau, eligible)}
    forward = valid_delta & (stage[:, 1:] > stage[:, :-1])
    forward_changes = {}
    for source, target in torch.stack((stage[:, :-1][forward], stage[:, 1:][forward]), 1).unique(dim=0).tolist():
        pair = forward & (stage[:, :-1] == source) & (stage[:, 1:] == target)
        forward_changes[f"{names[source]} -> {names[target]}"] = describe(delta[pair])
    correlations = []
    for episode in selected.nonzero().flatten().tolist():
        values = phi[episode, mask[episode]]
        correlation = spearman(values, torch.arange(values.numel()))
        if correlation is not None:
            correlations.append(correlation)
    dynamics = {
        "initial_phi": describe(phi[selected, 0]), "success_phi": describe(end_phi[selected]),
        "steps": int(valid_delta.sum()), "negative_step_fraction": fraction(negative, valid_delta),
        "stage_decrease_fraction": fraction(negative & regress, valid_delta),
        "same_stage_decrease_fraction": fraction(negative & same_stage, valid_delta),
        "negative_by_destination_stage": negative_rates,
        "negative_mass_per_episode": describe(negative_mass[selected]),
        "largest_single_drop": float((-delta[valid_delta]).clamp_min(0).max()) if valid_delta.any() else None,
        "no_negative_step_episode_fraction": fraction(~(negative & transition_mask).any(1), selected),
        "plateau_step_fraction": fraction(plateau, valid_delta), "plateau_by_destination_stage": plateaus,
        "forward_transitions": forward_changes,
        "spearman": {"mean": float(np.mean(correlations)) if correlations else None,
                     "defined_episodes": len(correlations),
                     "undefined_episodes": int(selected.sum()) - len(correlations)},
    }
    expected_phi = (stage + output["stage_progress"]) / len(names)
    difference = (phi - expected_phi).abs()[mask]
    identity = {"steps": int(mask.sum()), "exact": bool((difference == 0).all()),
                "mismatch_count": int((difference != 0).sum()), "max_abs_error": float(difference.max())}
    return {
        "a_chain": chain, "b_regressions": regressions, "c_timing": timing, "d_phi": dynamics,
        "e_official": official_correspondence(data, output, graph, instances),
        "f_failures": {"episodes": int(classes["failure"].sum()),
                       "last_stage_histogram": histogram(end_stage[classes["failure"]], names),
                       "last_phi": describe(end_phi[classes["failure"]])},
        "phi_identity": identity,
    }


def compare_candidates(data: dict, names: list[str]) -> dict:
    generated, reference = data["teachers"]["generated"], data["teachers"]["reference"]
    mask = data["mask"]
    difference = (generated["phi"] - reference["phi"]).abs()
    return {"steps": int(mask.sum()),
            "equal_stage_fraction": fraction(generated["stage"] == reference["stage"], mask),
            "abs_phi_difference": describe(difference[mask]),
            "by_generated_stage": {name: describe(difference[mask & (generated["stage"] == k)])
                                   for k, name in enumerate(names)}}


def summarize(data: dict, teachers: dict[str, Teacher], goal_thresh: float) -> dict:
    classes = episode_classes(data, goal_thresh)
    grasped = (data["official"]["is_grasped"] & data["official_mask"]).any(1)
    episodes = {key: int(value.sum()) for key, value in classes.items()}
    episodes.update(total=data["lengths"].numel(),
                    success_rate=classes["success"].double().mean().item(),
                    length_mean=data["lengths"].double().mean().item(),
                    non_trivial_success_never_grasped=int((classes["non_trivial_success"] & ~grasped).sum()),
                    failure_truncated_at_limit=int((classes["failure"] & data["truncated"] &
                                                    (data["lengths"] == 50)).sum()))
    return {"episodes": episodes,
            "candidates": {label: candidate_statistics(data, label, teacher.candidate.graph,
                                                       teacher.instances, goal_thresh)
                           for label, teacher in teachers.items()},
            "g_comparison": compare_candidates(data, teachers["generated"].stage_names)}


def sanity_check(data: dict, expected: dict) -> dict:
    subset = data["seed"] == 10001
    if not subset.any():
        return {"checked": False, "reason": "reset seed 10001 was not requested"}
    success = (data["official"]["success"] & data["official_mask"]).any(1)
    actual = {"episodes": int(subset.sum()), "success_once": success[subset].double().mean().item(),
              "length_mean": data["lengths"][subset].double().mean().item()}
    expected = {key: expected[key] for key in actual}
    matches = {key: actual[key] == expected[key] for key in actual}
    return {"checked": True, "actual": actual, "expected": expected,
            "matches": matches, "all_exact": all(matches.values())}


def format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.8g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def table(headers: list[str], rows: list) -> str:
    def row(values):
        return "| " + " | ".join(format_value(value).replace("|", "\\|").replace("\n", "<br>")
                                  for value in values) + " |"
    return "\n".join([row(headers), row(["---"] * len(headers)), *[row(values) for values in rows]]) + "\n\n"


def scalar_rows(values: dict, prefix: str = "") -> list:
    rows = []
    for key, value in values.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            rows.extend(scalar_rows(value, name))
        else:
            rows.append([name, value])
    return rows


def write_report(out: Path, config: dict, summary: dict, trajectories: dict,
                 teachers: dict[str, Teacher]) -> None:
    text = ["# PickCube teacher behavioral check\n\n", "## Method and run facts\n\n",
            "Both teachers observe the same policy actions and environment rewards before vector auto-reset. "
            "One GPU environment is reused for all resets. Each tensor row records only its first episode.\n\n",
            "Deterministic actions use the actor mean. Stochastic actions use the learned diagonal Gaussian, "
            "with one torch seed set before the entire stochastic set. Both are clamped to action bounds. "
            "Teacher parameters use candidate defaults. The policy is loaded with weights_only=True in eval mode.\n\n",
            "Timing includes t=0 and t=L. Entry means the first stage >= k, including skipped stages. "
            "Entry statistics condition on reaching that stage; skip fractions divide by all non-trivial successes. "
            "Phi rates divide by valid t>=1 steps, grouped by destination stage; regression and same-stage rates "
            "use the same denominator. Negative mass sums max(-dPhi, 0), including subthreshold changes. "
            "Drop/plateau classification uses 1e-4. Spearman uses average tied ranks and omits constant sequences "
            "from the mean, reporting their count. Quantiles use linear interpolation. Empty groups are null. "
            "Comparison g includes t=0 and groups by generated stage. No post-terminal step is included.\n\n",
            table(["Run item", "Value"], [["command", config["command"]], ["output", str(out)],
                  ["CUDA_VISIBLE_DEVICES", config["CUDA_VISIBLE_DEVICES"]], ["seeds", config["seeds"]],
                  ["stochastic_seed", config["stochastic_seed"]], ["git commit", config["git_commit"]],
                  ["ManiSkill", config["maniskill_version"]], ["wall_time_s", summary["wall_time_s"]],
                  ["trajectories_bytes", summary["trajectories_bytes"]]]),
            "### Reproduction of eval.json\n\n", table(["Metric", "Value"], scalar_rows(summary["sanity"]))]
    for mode in ("deterministic", "stochastic"):
        result = summary[mode]
        text.extend([f"## {mode.title()}: facts\n\n",
                     table(["Episode class / metric", "Value"], scalar_rows(result["episodes"]))])
        for label, candidate in result["candidates"].items():
            text.append(f"### {label}\n\n")
            for key, title in (("a_chain", "a. Chain coverage"), ("b_regressions", "b. Regressions"),
                               ("c_timing", "c. Stage timing and entry geometry"), ("d_phi", "d. Phi dynamics"),
                               ("e_official", "e. Official correspondence"), ("f_failures", "f. Failures"),
                               ("phi_identity", "Phi identity")):
                text.extend([f"#### {title}\n\n", table(["Metric", "Value"], scalar_rows(candidate[key]))])
        text.extend(["### g. Generated versus reference\n\n",
                     table(["Metric", "Value"], scalar_rows(result["g_comparison"]))])
    text.append("## Recorded traces\n\n")
    text.append("Selection is the first three qualifying episodes in seed/environment order. "
                "Deterministic traces require non-trivial success; stochastic traces require a regression "
                "in either teacher. Official fields at t=0 are unavailable. Margins retain the instance order "
                "printed above each table. Guidance is produced by Teacher.render from the recorded outputs.\n\n")
    for mode, data in trajectories.items():
        if mode == "deterministic":
            eligible = episode_classes(data, config["goal_thresh"])["non_trivial_success"]
        else:
            eligible = torch.zeros(data["lengths"].shape, dtype=torch.bool)
            for output in data["teachers"].values():
                eligible |= ((output["stage"][:, 1:] < output["stage"][:, :-1]) & data["mask"][:, 1:]).any(1)
        chosen = eligible.nonzero().flatten()[:3].tolist()
        text.append(f"### {mode}: {len(chosen)} episodes\n\n")
        for episode in chosen:
            text.append(f"Episode {episode}, seed {int(data['seed'][episode])}, "
                        f"environment {int(data['env_index'][episode])}.\n\n")
            for label, teacher in teachers.items():
                text.append(f"**{label}**. Margin order: {', '.join(teacher.instances)}.\n\n")
                rows = []
                for t in range(int(data["lengths"][episode]) + 1):
                    output = {key: value[episode, t].unsqueeze(0)
                              for key, value in data["teachers"][label].items()}
                    rows.append([t, teacher.stage_names[int(output["stage"][0])], float(output["phi"][0]),
                                 float(output["stage_progress"][0]),
                                 ", ".join(f"{value:.7g}" for value in output["margin"][0].tolist()),
                                 *[int(data["official"][key][episode, t]) if t else None for key in OFFICIAL],
                                 " ".join(teacher.render(output, 0))])
                text.append(table(["t", "stage", "Phi", "stage_progress", "margins", *OFFICIAL, "guidance"], rows))
    (out / "report.md").write_text("".join(text), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=POLICY)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--seeds", type=int, nargs="+", default=[10001, 10002, 10003, 10004])
    parser.add_argument("--stochastic-seed", type=int, default=20261027)
    args = parser.parse_args()
    if args.num_envs < 1:
        parser.error("--num-envs must be positive")
    args.policy = args.policy.resolve()
    if args.out is None:
        args.out = REPO_ROOT / "outputs/stage1/teacher_check" / datetime.now().strftime("%Y%m%d-%H%M%S")
    args.out = args.out.resolve()
    return args


def main() -> None:
    args = parse_args()
    start = time.perf_counter()
    args.out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    random.seed(1)
    np.random.seed(1)
    torch.manual_seed(1)
    torch.backends.cudnn.deterministic = True
    candidates = {label: load_candidate(path) for label, path in CANDIDATES.items()}
    expected = json.loads(args.policy.with_name("eval.json").read_text())
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    config.update(
        candidates={key: str(value) for key, value in CANDIDATES.items()},
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip(),
        git_status_before=subprocess.check_output(["git", "status", "--short"], cwd=REPO_ROOT, text=True),
        maniskill_version=version("mani_skill"), torch_version=torch.__version__,
        CUDA_VISIBLE_DEVICES=os.environ.get("CUDA_VISIBLE_DEVICES"),
        command="ulimit -c 0 && CUDA_VISIBLE_DEVICES=" + shlex.quote(os.environ.get("CUDA_VISIBLE_DEVICES", ""))
                + " " + shlex.join([sys.executable, *sys.argv]),
        env_id="PickCube-v1", obs_mode="state", control_mode="pd_joint_delta_pos", sim_backend="physx_cuda",
        render_mode=None, reward_mode="normalized_dense", max_episode_steps=50,
        ignore_terminations=False, record_metrics=True, auto_reset=True,
        initialization_seed=1, torch_deterministic=True, torch_num_threads=4,
        policy_config=json.loads(args.policy.with_name("config.json").read_text()),
    )
    envs = None
    try:
        import mani_skill.envs
        from mani_skill.utils.wrappers.flatten import FlattenActionSpaceWrapper
        from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv

        envs = gym.make("PickCube-v1", num_envs=args.num_envs, obs_mode="state",
                        control_mode="pd_joint_delta_pos", sim_backend="physx_cuda",
                        render_mode=None, reward_mode="normalized_dense")
        observer = TeacherObserver(envs, candidates)
        envs = observer
        if isinstance(envs.action_space, gym.spaces.Dict):
            envs = FlattenActionSpaceWrapper(envs)
        envs = ManiSkillVectorEnv(envs, args.num_envs, ignore_terminations=False,
                                 record_metrics=True, auto_reset=True)
        teachers = observer.teachers
        config.update(goal_thresh=float(envs.unwrapped.goal_thresh),
                      instances={label: teacher.instances for label, teacher in teachers.items()},
                      stages={label: teacher.stage_names for label, teacher in teachers.items()},
                      params={label: teacher.params for label, teacher in teachers.items()})
        (args.out / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        agent = Agent(envs).to(envs.device)
        agent.load_state_dict(torch.load(args.policy, map_location=envs.device, weights_only=True))
        agent.eval()
        trajectories = {}
        for mode in ("deterministic", "stochastic"):
            if mode == "stochastic":
                torch.manual_seed(args.stochastic_seed)
            batches = []
            for seed in args.seeds:
                data = rollout(agent, envs, seed, mode == "deterministic")
                batches.append(data)
                success = episode_classes(data, config["goal_thresh"])["success"].double().mean().item()
                print(f"{mode} seed={seed}: success_once={success} "
                      f"length_mean={data['lengths'].double().mean().item()}", flush=True)
            trajectories[mode] = concatenate_rollouts(batches)
    finally:
        if envs is not None:
            envs.close()
    torch.save(trajectories, args.out / "trajectories.pt")
    summary = {mode: summarize(data, teachers, config["goal_thresh"]) for mode, data in trajectories.items()}
    summary["sanity"] = sanity_check(trajectories["deterministic"], expected)
    summary["wall_time_s"] = time.perf_counter() - start
    summary["trajectories_bytes"] = (args.out / "trajectories.pt").stat().st_size
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_report(args.out, config, summary, trajectories, teachers)
    print(json.dumps({"out": str(args.out), "wall_time_s": summary["wall_time_s"],
                      "sanity": summary["sanity"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
