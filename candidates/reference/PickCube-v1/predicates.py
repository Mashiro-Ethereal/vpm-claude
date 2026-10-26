"""Measurement functions and predicates for PickCube-v1 (reference candidate)."""
import torch

from vpmkit.api import predicate, signed


def tcp_dist(w, g, o):
    """Distance (m) from the TCP of g to the center of o."""
    return torch.linalg.norm(g.pos - o.pos, dim=-1)  # meters


@predicate(
    desc=(
        "The TCP of g is within max_dist of the bounding sphere of o: its distance "
        "to the center of o is at most o's half diagonal plus max_dist."
    ),
    need_true="{g} is far from {o}; move {g} to {o}.",
    need_false="{g} is too close to {o}; move {g} away from {o}.",
    scale=0.3,
)
def near(w, g, o, max_dist=0.02):
    radius = torch.linalg.norm(o.half_size, dim=-1)  # half diagonal of the box of o
    return radius + max_dist - tcp_dist(w, g, o)  # meters


@predicate(
    desc="The gripper g holds o: both fingers press on o (the adapter's grasp reading).",
    need_true="{o} is not held; grasp {o} with {g}.",
    need_false="{o} is still held; release {o}.",
    scale=1.0,
)
def grasped(w, g, o):
    # Same reading as is_grasped in evaluate(): agent.is_grasping with its defaults.
    return signed(w.grasping(g, o))  # +1 held, -1 not held (dimensionless)


@predicate(
    desc="The center of o is within max_dist of the position of t (3-D Euclidean distance).",
    need_true="{o} is not at {t}; move {o} to {t}.",
    need_false="{o} is at {t}; move {o} away from {t}.",
    scale=0.3,
)
def at_goal(w, o, t, max_dist=0.025):
    # Same test as is_obj_placed in evaluate(): ||goal_site.p - cube.p|| <=
    # goal_thresh = 0.025 (the panda value).
    return max_dist - torch.linalg.norm(t.pos - o.pos, dim=-1)  # meters


@predicate(
    desc=(
        "The arm of g is at rest: every arm joint, fingers excluded, moves "
        "at most max_qvel rad/s."
    ),
    need_true="{g} is still moving; hold {g} still.",
    need_false="{g} is at rest; move {g}.",
    scale=1.0,
)
def arm_static(w, g, max_qvel=0.2):
    # Same test as Panda.is_static(0.2) in evaluate(): g.arm_qvel is the robot's
    # qvel without the two finger joints.
    return max_qvel - torch.max(torch.abs(g.arm_qvel), dim=1)[0]  # rad/s
