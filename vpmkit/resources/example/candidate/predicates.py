"""Measurement functions and predicates for PlaceCubeOnPad-v1 (example)."""
import torch

from vpmkit.api import predicate, signed


def tcp_dist(w, g, o):
    """Distance (m) from the TCP of g to the center of o."""
    return torch.linalg.norm(g.pos - o.pos, dim=-1)


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
    return signed(w.grasping(g, o))  # +1 held, -1 not held


@predicate(
    desc=(
        "o rests on t: horizontally, the center of o is within t's x half size minus "
        "o's x half size of the center of t; vertically, the bottom of o is within "
        "z_tol of the top of t."
    ),
    need_true="{o} is not on {t}; put {o} on {t}.",
    need_false="{o} is on {t}; lift {o} off {t}.",
    scale=0.2,
)
def on(w, o, t, z_tol=0.005):
    # Same formula as is_cube_on_pad in evaluate(); z_tol is the official 0.005.
    offset = o.pos - t.pos
    xy_room = t.half_size[:, 0] - o.half_size[:, 0]
    xy_margin = xy_room - torch.linalg.norm(offset[:, :2], dim=-1)
    gap = offset[:, 2] - o.half_size[:, 2] - t.half_size[:, 2]  # bottom of o above top of t
    z_margin = z_tol - torch.abs(gap)
    return torch.minimum(xy_margin, z_margin)  # meters


@predicate(
    desc=(
        "o is at rest: its linear speed is at most lin_thresh (m/s) and its angular "
        "speed at most ang_thresh (rad/s)."
    ),
    need_true="{o} is still moving; hold still until {o} comes to rest.",
    need_false="{o} is at rest; move {o}.",
    scale=1.0,
)
def static(w, o, lin_thresh=1e-2, ang_thresh=0.5):
    # Same test as Actor.is_static(lin_thresh=1e-2, ang_thresh=0.5) in evaluate().
    lin = torch.linalg.norm(o.lin_vel, dim=-1)
    ang = torch.linalg.norm(o.ang_vel, dim=-1)
    lin_slack = (lin_thresh - lin) / lin_thresh
    ang_slack = (ang_thresh - ang) / ang_thresh
    return torch.minimum(lin_slack, ang_slack)  # fraction of the speed limit
