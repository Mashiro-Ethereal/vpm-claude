"""JSON and Markdown inventories of ManiSkill scenes across reset seeds."""

import json

import torch

from ..geometry import quat_to_matrix
from .maniskill import make_env


def _numeric_attributes(env):
    # Include plain class constants (e.g. PushCube.cube_half_size), but do not
    # evaluate properties or traverse scene/agent objects.
    values = {}
    for cls in reversed(type(env).__mro__):
        values.update(vars(cls))
    values.update(vars(env))
    result = {}
    for key, value in sorted(values.items()):
        if key.startswith("_"):
            continue
        if type(value) in (int, float):
            result[key] = value
        elif isinstance(value, torch.Tensor) and value.numel() <= 16 and not value.is_complex():
            result[key] = {"value": value.detach().cpu().tolist(),
                           "dtype": str(value.dtype), "shape": list(value.shape)}
    return result


def scene_inventory(env_id, seeds=(0, 1, 2, 3, 4)) -> dict:
    """Sample a single CPU environment; ranges aggregate every supplied seed.

    Yaw is world heading atan2(R[1,0], R[0,0]), in radians in [-pi, pi].
    Numeric attributes and evaluation schemas describe the final reset.
    """
    seeds = tuple(seeds)
    if not seeds:
        raise ValueError("scene_inventory requires at least one seed")
    env = make_env(env_id)
    try:
        base = env.unwrapped
        actors = {}
        for seed in seeds:
            env.reset(seed=seed)
            for actor in base.scene.actors.values():
                pose = actor.pose
                pos = pose.p.detach().cpu()
                matrix = quat_to_matrix(pose.q)
                yaw = torch.atan2(matrix[..., 1, 0], matrix[..., 0, 0]).detach().cpu()
                if actor.name not in actors:
                    actors[actor.name] = {"name": actor.name, "body_type": actor.px_body_type,
                                          "positions": [], "yaws": []}
                actors[actor.name]["positions"].append(pos)
                actors[actor.name]["yaws"].append(yaw)
        for entry in actors.values():
            positions = torch.cat(entry.pop("positions"))
            yaws = torch.cat(entry.pop("yaws"))
            entry["position_min"] = positions.amin(0).tolist()
            entry["position_max"] = positions.amax(0).tolist()
            entry["yaw_range"] = [yaws.min().item(), yaws.max().item()]
        return {
            "env_id": env_id, "seeds": list(seeds), "num_envs": base.num_envs,
            "actors": list(actors.values()),
            "evaluate": {key: {"dtype": str(torch.as_tensor(value).dtype),
                               "shape": list(torch.as_tensor(value).shape)}
                         for key, value in base.evaluate().items()},
            "agent": {"uid": base.agent.uid, "control_mode": base.agent.control_mode},
            "numeric_attributes": _numeric_attributes(base),
        }
    finally:
        env.close()


def inventory_markdown(inv) -> str:
    lines = [f"# {inv['env_id']}", "", f"Seeds: {inv['seeds']}", "",
             f"Agent: {inv['agent']['uid']}; control mode: {inv['agent']['control_mode']}", "",
             "| Actor | Body type | Position min | Position max | Yaw range (rad) |",
             "| --- | --- | --- | --- | --- |"]
    for actor in inv["actors"]:
        lines.append(f"| {actor['name']} | {actor['body_type']} | {actor['position_min']} | "
                     f"{actor['position_max']} | {actor['yaw_range']} |")
    lines += ["", "## Evaluation", "", "| Key | Dtype | Shape |", "| --- | --- | --- |"]
    for key, value in inv["evaluate"].items():
        lines.append(f"| {key} | {value['dtype']} | {value['shape']} |")
    lines += ["", "## Numeric attributes (final reset)", "", "```json",
              json.dumps(inv["numeric_attributes"], indent=2), "```", ""]
    return "\n".join(lines)
