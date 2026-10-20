"""ManiSkill 3 bindings and snapshots for Panda tabletop tasks."""

from itertools import combinations
import os
from pathlib import Path

os.environ.setdefault("MS_ASSET_DIR", str(Path(__file__).resolve().parents[2] / "outputs/ms_assets"))

import torch

from ..world import BindingAPI, ObjSpec, ObjState, WorldState


class AdapterError(ValueError):
    """A binding cannot be represented by a batched WorldState."""


def make_env(env_id, num_envs=1, seed=None, **kwargs):
    """Create a state-only environment, optionally resetting it with a seed."""
    import gymnasium as gym
    import mani_skill.envs  # Register tasks after setting MS_ASSET_DIR.
    import sapien.physx as physx

    # This runtime has CUDA. SAPIEN requires GPU initialization before *any*
    # scene, including a CPU inventory, if a batched GPU env will be used later.
    physx.enable_gpu()

    env = gym.make(
        env_id, num_envs=num_envs, obs_mode="state", render_mode=None,
        sim_backend="physx_cuda" if num_envs > 1 else "physx_cpu", **kwargs,
    )
    if seed is not None:
        try:
            env.reset(seed=seed)
        except Exception:
            env.close()
            raise
    return env


class ManiSkillBindingAPI(BindingAPI):
    def __init__(self, env):
        self.env = env.unwrapped

    def gripper(self):
        return ObjSpec(kind="gripper", source=self.env.agent)

    def actor(self, actor, half_size, attrs=None):
        return ObjSpec(kind="actor", source=actor, half_size=half_size,
                       attrs={} if attrs is None else attrs)

    def site(self, source, attrs=None):
        return ObjSpec(kind="site", source=source, half_size=0.0,
                       attrs={} if attrs is None else attrs)

    def table(self):
        return ObjSpec(kind="table", source=None, half_size=(1.0, 1.0, 0.01))


def _batch(value, n, device, label, tail=None, dtype=None):
    """Materialize scalars or tensors with leading dimension 1/N.

    With a fixed tail, an unbatched vector (e.g. half_size [3]) also broadcasts.
    General vector attributes use [1,D] for constants and [N,D] per environment.
    """
    value = value() if callable(value) else value
    try:
        tensor = torch.as_tensor(value, device=device)
    except (TypeError, ValueError, RuntimeError) as exc:
        raise AdapterError(f"{label}: expected numeric data: {exc}") from exc
    if tensor.is_complex():
        raise AdapterError(f"{label}: expected real numeric data")
    tensor = tensor.to(dtype=dtype or (torch.bool if tensor.dtype == torch.bool else torch.float32))
    shape = (n, *tail) if tail is not None else (n, *tensor.shape[1:])
    try:
        if tail is not None and tensor.ndim > 0 and tuple(tensor.shape) not in (
            tail, (1, *tail), shape,
        ):
            raise ValueError("incorrect dimensions")
        if tail is None and tensor.ndim > 0 and tensor.shape[0] not in (1, n):
            raise ValueError("incorrect leading dimension")
        tensor = torch.broadcast_to(tensor, shape)
    except (RuntimeError, ValueError) as exc:
        raise AdapterError(f"{label}: expected shape {shape}, got {tuple(tensor.shape)}") from exc
    # Simulator buffers and callable attrs can be mutated by subsequent steps/resets.
    return tensor.clone()


def _official(env):
    return {key: _batch(value, env.num_envs, env.device, f"official[{key!r}]")
            for key, value in env.evaluate().items()}


class ManiSkillAdapter:
    def __init__(self, env, bind_fn):
        self.env = env.unwrapped
        self.N = self.env.num_envs
        self.device = self.env.device
        self.bindings = bind_fn(self.env, ManiSkillBindingAPI(self.env))
        if not isinstance(self.bindings, dict):
            raise AdapterError("bind must return a dict mapping handles to ObjSpec")
        for handle, spec in self.bindings.items():
            if not isinstance(handle, str) or not isinstance(spec, ObjSpec):
                raise AdapterError(f"binding {handle!r}: expected a string handle and ObjSpec")
            if spec.kind not in {"actor", "site", "gripper", "table"}:
                raise AdapterError(f"binding {handle!r}: unknown kind {spec.kind!r}")
            if not isinstance(spec.attrs, dict) or any(not isinstance(k, str) for k in spec.attrs):
                raise AdapterError(f"binding {handle!r}: attrs must map string keys to numeric data")
            self._object(handle, spec)

    def _actor_source(self, source):
        # CPU PegInsertionSide rebuilds its actors on reset. Bind once, then
        # resolve the same named actor/view in the current scene each snapshot.
        registry = self.env.scene.actor_views if source.merged else self.env.scene.actors
        try:
            return registry[source.name]
        except KeyError as exc:
            raise AdapterError(f"bound actor {source.name!r} is absent from the current scene") from exc

    def _object(self, handle, spec):
        def batch(value, field, tail=None, dtype=torch.float32):
            return _batch(value, self.N, self.device, f"{handle}.{field}", tail, dtype)

        attrs = {key: batch(value, f"attrs[{key!r}]") for key, value in spec.attrs.items()}
        zero = torch.zeros((self.N, 3), device=self.device, dtype=torch.float32)
        linvel, angvel, half_size = zero.clone(), zero.clone(), zero.clone()
        try:
            if spec.kind == "table":
                pos = batch((0.0, 0.0, -0.01), "pos", (3,))
                quat = batch((1.0, 0.0, 0.0, 0.0), "quat", (4,))
                half_size = batch((1.0, 1.0, 0.01), "half_size", (3,))
            else:
                source = spec.source
                if spec.kind == "gripper":
                    source = self.env.agent
                    body = source.tcp
                    pose = body.pose
                    attrs["width"] = batch(source.robot.get_qpos()[:, -2:].sum(-1), "width", ())
                    attrs["arm_qvel"] = batch(source.robot.get_qvel()[:, :-2], "arm_qvel")
                    linvel = batch(body.linear_velocity, "linvel", (3,))
                    angvel = batch(body.angular_velocity, "angvel", (3,))
                elif spec.kind == "site":
                    pose = source() if callable(source) else self._actor_source(source).pose
                else:
                    source = self._actor_source(source)
                    pose = source.pose
                    half_size = batch(spec.half_size, "half_size", (3,))
                    try:
                        linvel = batch(source.linear_velocity, "linvel", (3,))
                        angvel = batch(source.angular_velocity, "angvel", (3,))
                    except AttributeError:
                        if source.px_body_type not in {"kinematic", "static"}:
                            raise
                pos = batch(pose.p, "pos", (3,))
                quat = batch(pose.q, "quat", (4,))
        except AttributeError as exc:
            raise AdapterError(f"binding {handle!r} ({spec.kind}): {exc}") from exc
        return ObjState(pos, quat, linvel, angvel, half_size, spec.kind, attrs)

    def snapshot(self) -> WorldState:
        objects = {handle: self._object(handle, spec) for handle, spec in self.bindings.items()}
        actors = {h: self._actor_source(s.source) for h, s in self.bindings.items() if s.kind == "actor"}
        grasping = {
            (g, a): _batch(self.env.agent.is_grasping(actor), self.N, self.device,
                           f"grasping[{g!r}, {a!r}]", (), torch.bool)
            for g, spec in self.bindings.items() if spec.kind == "gripper"
            for a, actor in actors.items()
        }
        contacts = {
            (a, b): _batch(torch.linalg.vector_norm(
                self.env.scene.get_pairwise_contact_forces(actors[a], actors[b]), dim=-1,
            ), self.N, self.device, f"contacts[{a!r}, {b!r}]", (), torch.float32)
            for a, b in combinations(actors, 2)
        }
        world = WorldState(
            self.N, self.device, objects, grasping, contacts, _official(self.env),
            {"env_id": self.env.spec.id, "num_envs": self.N},
        )
        try:
            world.validate()
        except ValueError as exc:
            raise AdapterError(str(exc)) from exc
        return world


class MilestoneTracker:
    """Candidate-independent readings. Call reset after resetting the environment.

    Actors confined to one sub-scene retain their scene names; their readings are
    false in rows where they do not exist (e.g. PegInsertionSide's peg_0).
    """

    def __init__(self, env):
        self.env = env.unwrapped
        self.z_at_reset = {}
        self.reset()

    def reset(self, env_idx=None):
        self.actors = {a.name: a for a in self.env.scene.actors.values()
                       if a.px_body_type == "dynamic"}
        mask = torch.zeros(self.env.num_envs, device=self.env.device, dtype=torch.bool)
        mask[:] = env_idx is None
        if env_idx is not None:
            mask[env_idx] = True
        for name, actor in self.actors.items():
            idx = actor._scene_idxs.long()
            if env_idx is None or name not in self.z_at_reset:
                self.z_at_reset[name] = torch.zeros(self.env.num_envs, device=self.env.device)
            selected = mask[idx]
            self.z_at_reset[name][idx[selected]] = actor.pose.p[selected, 2]

    def _grasp_source(self, actor):
        if len(actor._objs) == self.env.num_envs:
            return actor
        # is_grasping pairs bodies by row, so a single-scene actor must be queried
        # through its full merged view to pair it with the correct robot fingers.
        for view in self.env.scene.actor_views.values():
            if len(view._objs) == self.env.num_envs and all(
                view._objs[i] is obj for i, obj in zip(actor._scene_idxs.tolist(), actor._objs)
            ):
                return view
        raise AdapterError(f"actor {actor.name!r}: no full-batch view for grasp queries")

    def read(self) -> dict[str, torch.Tensor]:
        readings = {}
        for key, value in _official(self.env).items():
            if value.dtype == torch.bool:
                if value.shape != (self.env.num_envs,):
                    raise AdapterError(f"official:{key}: milestones require shape [{self.env.num_envs}]")
                readings[f"official:{key}"] = value
        for name, actor in self.actors.items():
            idx = actor._scene_idxs.long()
            grasped = torch.zeros(self.env.num_envs, device=self.env.device, dtype=torch.bool)
            lifted = torch.zeros_like(grasped)
            grasped[idx] = self.env.agent.is_grasping(self._grasp_source(actor))[idx]
            lifted[idx] = actor.pose.p[:, 2] - self.z_at_reset[name][idx] > 0.02
            readings[f"grasped:{name}"] = grasped
            readings[f"lifted:{name}"] = lifted
        return readings


def random_rollout(env, adapter, steps, seed) -> list[WorldState]:
    """Snapshot reset and each step with seeded uniform Box-space actions."""
    env.reset(seed=seed)
    env.action_space.seed(seed)
    frames = [adapter.snapshot()]
    for _ in range(steps):
        env.step(env.action_space.sample())
        frames.append(adapter.snapshot())
    return frames
