"""Trajectory storage, simulator state replay, and temporal diagnostics."""

from collections import Counter
from dataclasses import dataclass
import math
from statistics import median

import torch

from ..artifact.literals import parse_literal
from ..world import WorldState


@dataclass
class Trajectory:
    states: WorldState
    success: bool
    source: str


def save_trajectories(path, trajs):
    torch.save([{"states": t.states.to("cpu").to_dict(), "success": t.success, "source": t.source}
                for t in trajs], path)


def load_trajectories(path) -> list[Trajectory]:
    return [Trajectory(WorldState.from_dict(t["states"]), t["success"], t["source"])
            for t in torch.load(path, map_location="cpu", weights_only=True)]


def replay_env_states(env, adapter, env_states) -> WorldState:
    """Restore and snapshot each state without advancing physics; requires N=1."""
    if env.unwrapped.num_envs != 1:
        raise ValueError("A trajectory requires num_envs=1")
    frames = []
    for state in env_states:
        env.unwrapped.set_state_dict(state)
        frames.append(adapter.snapshot())
    return WorldState.cat(frames)


def record_rollout(env, adapter, policy_fn, steps, seed) -> Trajectory:
    """Record reset plus each step. policy_fn receives the current observation."""
    if env.unwrapped.num_envs != 1:
        raise ValueError("A trajectory requires num_envs=1")
    obs, _ = env.reset(seed=seed)
    env.action_space.seed(seed)
    frames = [adapter.snapshot()]
    for _ in range(steps):
        obs, _, _, _, _ = env.step(policy_fn(obs))
        frames.append(adapter.snapshot())
    success = bool(env.unwrapped.evaluate()["success"][0])
    return Trajectory(WorldState.cat(frames), success, f"rollout:seed={seed}")


def _spearman(values):
    """Correlation with frame order, using average ranks for ties."""
    n = len(values)
    if n < 2:
        return None
    order = sorted(range(n), key=values.__getitem__)
    ranks = [0.0] * n
    start = 0
    while start < n:
        end = start + 1
        while end < n and values[order[end]] == values[order[start]]:
            end += 1
        for i in order[start:end]:
            ranks[i] = (start + end - 1) / 2
        start = end
    center = (n - 1) / 2
    x, y = [i - center for i in range(n)], [r - center for r in ranks]
    denom = math.sqrt(sum(v * v for v in x) * sum(v * v for v in y))
    return sum(a * b for a, b in zip(x, y)) / denom if denom else None


def _summarize_replays(teacher, trajectories, outputs):
    names = [s.name for s in teacher.candidate.graph.stages] + ["done"]
    indices = {key: i for i, key in enumerate(teacher.instance_keys)}
    literals = dict.fromkeys(text for stage in teacher.candidate.graph.stages
                             for text in [*stage.exit, *(inv.literal for inv in stage.invariants)])
    for decl in teacher.candidate.graph.official:
        literals.update(dict.fromkeys(decl.literals))
    reached_counts, stuck_counts = Counter(), Counter()
    durations = {name: [] for name in names}
    records = []
    for traj, out in zip(trajectories, outputs):
        stages = out.stage.tolist()
        if not stages:
            raise ValueError(f"Trajectory {traj.source!r} has no frames")
        progress, phi = out.stage_progress.tolist(), out.phi.tolist()
        transitions, jumps, segments = [], [], []
        reached = {0}
        previous = 0
        # At frame zero compare potential before/after the first automaton update.
        previous_phi = float(out.progress_raw[0, 0].clamp(0, 1)) / teacher.K
        for frame, stage in enumerate(stages):
            if stage != previous:
                transition = {"frame": frame, "from": names[previous], "to": names[stage]}
                transitions.append(transition)
                jumps.append({**transition, "delta": phi[frame] - previous_phi})
                reached.update(range(previous, stage + 1) if stage > previous else [stage])
            previous, previous_phi = stage, phi[frame]
        start = 0
        for end in range(1, len(stages) + 1):
            if end == len(stages) or stages[end] != stages[start]:
                segments.append({"stage": names[stages[start]], "start_frame": start,
                                 "end_frame": end - 1, "frames": end - start,
                                 "spearman": _spearman(progress[start:end])})
                start = end
        for stage in reached:
            name = names[stage]
            reached_counts[name] += 1
            durations[name].append(stages.count(stage))
        flicker = {}
        for text in literals:
            lit = parse_literal(text)
            value = out.value[:, indices[lit.instance_key]]
            flicker[text] = int((value[1:] != value[:-1]).sum())
        stuck = None
        if stages[-1] != teacher.K:
            stage = stages[-1]
            unmet = []
            for text in teacher.candidate.graph.stages[stage].exit:
                lit = parse_literal(text)
                idx = indices[lit.instance_key]
                if bool(out.value[-1, idx]) != lit.positive:
                    spec = teacher.candidate.predicate_specs[lit.pred]
                    thresholds = {key: teacher.candidate.params.get(f"{lit.pred}.{key}", default)
                                  for key, default in spec.thresholds.items()}
                    unmet.append({"literal": text, "margin": float(out.margin[-1, idx]),
                                  "thresholds": thresholds})
                    stuck_counts[text] += 1
            frames = [i for i, k in enumerate(stages) if k == stage]
            stuck = {"stage": names[stage], "unmet_exit_literals": unmet,
                     "max_progress_frame": max(frames, key=progress.__getitem__)}
        records.append({
            "source": traj.source, "success": traj.success, "num_frames": len(stages),
            "transitions": transitions,
            "regressions": [{"frame": i, "event": teacher.render_event(out.event[i])}
                            for i in range(len(stages)) if bool(out.regressed[i])],
            "final_stage": names[stages[-1]], "done": bool(out.done[-1]),
            "reached_done": bool(out.done.any()), "stuck": stuck,
            "stage_segments": segments, "phi_jumps": jumps, "literal_flicker": flicker,
        })
    n = len(records)
    return {"trajectories": records, "aggregate": {
        "num_trajectories": n,
        "fraction_reaching_stage": {name: reached_counts[name] / n if n else 0.0 for name in names},
        "median_frames_per_stage": {name: median(v) if v else None for name, v in durations.items()},
        "most_frequent_stuck_literal": stuck_counts.most_common(1)[0][0] if stuck_counts else None,
    }}


def replay_summary(teacher, trajectories) -> dict:
    """Summarize post-step stages; count immediately crossed stages as reached.

    Frame medians use total occupancy per trajectory that reached the stage,
    including zero for a stage crossed immediately. Undefined correlations are null.
    """
    outputs = [teacher.run_sequence(t.states.to(teacher.device)) for t in trajectories]
    return _summarize_replays(teacher, trajectories, outputs)
