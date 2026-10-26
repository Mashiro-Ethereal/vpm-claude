"""Human-maintained helper descriptions and task call sites."""

from collections.abc import Callable
from dataclasses import dataclass
import inspect
import textwrap


@dataclass
class Helper:
    id: str
    defined_at: str
    candidate_use: str
    source_included: bool
    source: Callable[[], str]


def _source(*objects: Callable) -> str:
    return "\n".join(textwrap.dedent(inspect.getsource(obj)) for obj in objects)


def _is_grasping_source() -> str:
    from mani_skill.agents.robots.panda.panda import Panda

    return _source(Panda.is_grasping)


def _panda_static_source() -> str:
    from mani_skill.agents.robots.panda.panda import Panda

    return _source(Panda.is_static)


def _actor_static_source() -> str:
    from mani_skill.utils.structs.actor import Actor

    return _source(Actor.is_static)


def _rotation_source() -> str:
    from mani_skill.utils.geometry.rotation_conversions import quaternion_to_matrix, matrix_to_euler_angles

    return _source(quaternion_to_matrix, matrix_to_euler_angles)


def _pose_source() -> str:
    from mani_skill.utils.structs.pose import Pose

    return _source(Pose.inv, Pose.__mul__)


HELPERS = {
    "is_grasping": Helper(
        "is_grasping", "Panda.is_grasping (mani_skill/agents/robots/panda/panda.py)",
        "Use the adapter reading w.grasping(g, o): it calls self.agent.is_grasping(obj) "
        "with its default arguments (min_force=0.5, max_angle=85).",
        False, _is_grasping_source),
    "Panda.is_static": Helper(
        "Panda.is_static", "Panda.is_static (mani_skill/agents/robots/panda/panda.py)",
        "In a candidate, self.robot.get_qvel()[..., :-2] is the gripper view field g.arm_qvel.",
        True, _panda_static_source),
    "Actor.is_static": Helper(
        "Actor.is_static", "Actor.is_static (mani_skill/utils/structs/actor.py)",
        "In a candidate, self.linear_velocity and self.angular_velocity are the object view fields o.lin_vel and o.ang_vel.",
        True, _actor_static_source),
    "quaternion_to_matrix / matrix_to_euler_angles": Helper(
        "quaternion_to_matrix / matrix_to_euler_angles", "mani_skill/utils/geometry/rotation_conversions.py",
        "Use G.quat_to_euler_xyz.", False, _rotation_source),
    "Pose.inv / Pose multiplication": Helper(
        "Pose.inv / Pose multiplication", "mani_skill/utils/structs/pose.py",
        "Use G.pose_inv, G.pose_mul, G.to_local.", False, _pose_source),
}

TASK_HELPERS = {
    "PickCube-v1": [
        ("is_grasping", "self.agent.is_grasping(self.cube)"),
        ("Panda.is_static", "self.agent.is_static(0.2)"),
    ],
}
