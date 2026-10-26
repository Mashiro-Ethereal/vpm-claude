"""Sample a scene inventory in a process with no previous GPU environment."""

import ast
import inspect
from numbers import Real
import textwrap
from typing import Any

import mani_skill
import numpy as np
import torch
from mani_skill.utils.geometry.trimesh_utils import get_actor_visual_mesh
from mani_skill.utils.structs.actor import Actor

from ...geometry import quat_to_euler_xyz
from .env import make_env


def _number(value: float, fixed: bool = False) -> str:
    if round(float(value), 3) == 0:
        return "0"
    text = f"{value:.3f}"
    return (text if fixed else text.rstrip("0").rstrip(".")).replace("-", "−")


def _value(value: Any) -> str:
    array = np.asarray(value)
    if array.ndim:
        return "[" + ", ".join(_value(item) for item in array) + "]"
    if array.dtype.kind == "b":
        return str(bool(array))
    return _number(float(array))


def _range(low: float, high: float, fixed: bool = False) -> str:
    lo, hi = _number(low, fixed), _number(high, fixed)
    return lo if lo == hi else f"{lo} … {hi}"


def _axes(values: np.ndarray) -> str:
    return ", ".join(f"{axis} {_range(low, high, fixed=True)}"
                     for axis, low, high in zip("xyz", values.min(0), values.max(0)))


def _sample_value(values: np.ndarray) -> tuple[str, str]:
    if np.all(values == values[0]):
        return _value(values[0]), "yes"
    low, high = values.min(0), values.max(0)
    ranges = [_range(lo, hi) for lo, hi in zip(low.reshape(-1), high.reshape(-1))]
    return (ranges[0] if low.ndim == 0 else "[" + ", ".join(ranges) + "]"), "no"


def _half_sizes(actor: Actor) -> str:
    if actor.has_collision_shapes:
        meshes = actor.get_collision_meshes(to_world_frame=False)
    else:
        meshes = [get_actor_visual_mesh(obj) for obj in actor._objs]
    if not meshes or any(mesh is None for mesh in meshes):
        return "—"
    sizes = np.stack([(mesh.bounds[1] - mesh.bounds[0]) / 2 for mesh in meshes])
    value, same = _sample_value(sizes)
    return f"{value} in all environments" if same == "yes" else f"{value} across environments"


def _evaluate_attributes(env: Any) -> list[tuple[str, str, str]]:
    owner = next(cls for cls in type(env).__mro__ if "evaluate" in vars(cls))
    tree = ast.parse(textwrap.dedent(inspect.getsource(owner.evaluate)))
    reads = sorted((node for node in ast.walk(tree)
                    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)
                    and isinstance(node.value, ast.Name) and node.value.id == "self"),
                   key=lambda node: (node.lineno, node.col_offset))
    rows = []
    for name in dict.fromkeys(node.attr for node in reads):
        value = getattr(env, name)
        if not isinstance(value, (Real, list, tuple, np.ndarray, torch.Tensor)):
            continue
        array = value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else np.asarray(value)
        if array.dtype.kind not in "bifu":
            continue
        if isinstance(value, (torch.Tensor, np.ndarray)) and array.ndim and array.shape[0] == env.num_envs:
            formatted, same = _sample_value(array)
        else:
            formatted, same = _value(array), "yes"
        rows.append((name, formatted, same))
    return rows


def _reading_type(value: Any) -> str:
    tensor = torch.as_tensor(value)
    kind = "bool" if tensor.dtype == torch.bool else "float" if tensor.is_floating_point() else "int"
    shape = ", ".join(["N", *(str(dim) for dim in tensor.shape[1:])]) if tensor.ndim else ""
    return f"{kind} [{shape}]" if shape else kind


def scene_inventory(env_id: str, seeds: tuple[int, ...] = (0, 1, 2), num_envs: int = 8) -> str:
    """Create exactly one environment, sample one reset per seed, then close it.

    For num_envs > 1, call this in a fresh subprocess because SAPIEN permits
    only one GPU environment per process.
    """
    env = make_env(env_id, num_envs=num_envs)
    try:
        task = env.unwrapped
        samples: dict[str, list[torch.Tensor]] = {}
        for seed in seeds:
            env.reset(seed=seed)
            actors = {name: value for name, value in vars(task).items() if isinstance(value, Actor)}
            for name, actor in actors.items():
                samples.setdefault(name, []).append(actor.pose.raw_pose.detach().cpu().clone())
        lines = [f"# Scene inventory: {env_id}", "",
                 "This file was generated from the running environment.", "",
                 f"- ManiSkill {mani_skill.__version__}; robot `{task.robot_uids}`. The table top is at z = 0 (`w.table_z`).",
                 f"- Initial states sampled: {len(seeds)} seeds × {num_envs} parallel environments = {len(seeds) * num_envs}.",
                 "- Units: m, rad. World frame with z up; quaternions (w, x, y, z).", "",
                 "## Objects", "",
                 "| Attribute | Actor name | Kind | Half size (m) | Initial position (m), min … max | Initial orientation (XYZ Euler, rad), min … max |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for name, actor in actors.items():
            poses = torch.cat(samples[name])
            kind = actor.px_body_type if actor.has_collision_shapes else "visual only"
            positions = _axes(poses[:, :3].numpy())
            angles = _axes(quat_to_euler_xyz(poses[:, 3:]).numpy())
            lines.append(f"| `env.{name}` | `{actor.name}` | {kind} | {_half_sizes(actor)} | {positions} | {angles} |")
        robot = task.agent.robot
        opening, _ = _sample_value(robot.get_qlimits()[:, -2:, 1].sum(-1).cpu().numpy())
        lines.extend(["", "Kinds: dynamic (moved by physics), kinematic (moved only by the task code), visual only (no collision).", "",
                      "## Robot", "", "| Part | Value |", "| --- | --- |",
                      f"| Gripper | Panda two-finger gripper. TCP: link `{task.agent.tcp.name}`, between the fingertips. Full opening {opening} m |",
                      f"| Arm | {robot.get_qvel().shape[-1] - 2} joints, plus 2 finger joints |", "",
                      "## evaluate() keys", "", "| Key | Type |", "| --- | --- |"])
        lines.extend(f"| `{key}` | {_reading_type(value)} |" for key, value in task.evaluate().items())
        lines.extend(["", "## Attribute values read by evaluate()", "",
                      "| Attribute | Value | Same in all environments |", "| --- | --- | --- |"])
        lines.extend(f"| `self.{name}` | {value} | {same} |" for name, value, same in _evaluate_attributes(task))
        result = "\n".join(lines) + "\n"
        if "reward" in result.lower():
            raise ValueError("scene inventory contains forbidden text: reward")
        return result
    finally:
        env.close()
