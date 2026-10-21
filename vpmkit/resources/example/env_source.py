# Example environment for the candidate example. The task is fictional: it is
# written in the style of ManiSkill's tabletop tasks but is not part of
# ManiSkill. As in every input package, the two reward functions are removed.
from typing import Any

import numpy as np
import sapien
import torch

import mani_skill.envs.utils.randomization as randomization
from mani_skill.agents.robots import Panda
from mani_skill.envs.sapien_env import BaseEnv
from mani_skill.sensors.camera import CameraConfig
from mani_skill.utils import common, sapien_utils
from mani_skill.utils.building import actors
from mani_skill.utils.registration import register_env
from mani_skill.utils.scene_builder.table import TableSceneBuilder
from mani_skill.utils.structs.pose import Pose


@register_env("PlaceCubeOnPad-v1", max_episode_steps=50)
class PlaceCubeOnPadEnv(BaseEnv):
    """
    **Task Description:**
    Pick up a red cube, place it on a green target pad that lies on the table, and let go of it.

    **Randomizations:**
    - the cube's xy position is randomized on top of the table in the region [-0.12, -0.04] x [-0.1, 0.1], and its z-axis rotation is randomized
    - the pad's xy position is randomized on top of the table in the region [0.04, 0.12] x [-0.1, 0.1]; the pad is not rotated

    **Success Conditions:**
    - the cube rests on the pad: in the xy plane its center is within 0.03 m (the pad's half size minus the cube's half size) of the pad's center, and its bottom is within 0.005 m of the pad's top
    - the cube is static
    - the cube is not being grasped by the robot (robot must let go of the cube)
    """

    SUPPORTED_ROBOTS = ["panda"]
    agent: Panda

    def __init__(self, *args, robot_uids="panda", robot_init_qpos_noise=0.02, **kwargs):
        self.robot_init_qpos_noise = robot_init_qpos_noise
        super().__init__(*args, robot_uids=robot_uids, **kwargs)

    @property
    def _default_sensor_configs(self):
        pose = sapien_utils.look_at(eye=[0.3, 0, 0.6], target=[-0.1, 0, 0.1])
        return [CameraConfig("base_camera", pose, 128, 128, np.pi / 2, 0.01, 100)]

    @property
    def _default_human_render_camera_configs(self):
        pose = sapien_utils.look_at([0.6, 0.7, 0.6], [0.0, 0.0, 0.35])
        return CameraConfig("render_camera", pose, 512, 512, 1, 0.01, 100)

    def _load_agent(self, options: dict):
        super()._load_agent(options, sapien.Pose(p=[-0.615, 0, 0]))

    def _load_scene(self, options: dict):
        self.cube_half_size = common.to_tensor([0.02] * 3, device=self.device)
        self.pad_half_size = common.to_tensor([0.05, 0.05, 0.005], device=self.device)
        self.table_scene = TableSceneBuilder(
            env=self, robot_init_qpos_noise=self.robot_init_qpos_noise
        )
        self.table_scene.build()
        self.cube = actors.build_cube(
            self.scene,
            half_size=0.02,
            color=[1, 0, 0, 1],
            name="cube",
            initial_pose=sapien.Pose(p=[-0.08, 0, 0.02]),
        )
        self.pad = actors.build_box(
            self.scene,
            half_sizes=[0.05, 0.05, 0.005],
            color=[0, 1, 0, 1],
            name="pad",
            body_type="kinematic",
            initial_pose=sapien.Pose(p=[0.08, 0, 0.005]),
        )

    def _initialize_episode(self, env_idx: torch.Tensor, options: dict):
        with torch.device(self.device):
            b = len(env_idx)
            self.table_scene.initialize(env_idx)

            xyz = torch.zeros((b, 3))
            xyz[:, 0] = torch.rand((b,)) * 0.08 - 0.12
            xyz[:, 1] = torch.rand((b,)) * 0.2 - 0.1
            xyz[:, 2] = self.cube_half_size[2]
            qs = randomization.random_quaternions(b, lock_x=True, lock_y=True)
            self.cube.set_pose(Pose.create_from_pq(p=xyz, q=qs))

            pad_xyz = torch.zeros((b, 3))
            pad_xyz[:, 0] = torch.rand((b,)) * 0.08 + 0.04
            pad_xyz[:, 1] = torch.rand((b,)) * 0.2 - 0.1
            pad_xyz[:, 2] = self.pad_half_size[2]
            self.pad.set_pose(Pose.create_from_pq(p=pad_xyz))

    def evaluate(self):
        offset = self.cube.pose.p - self.pad.pose.p
        xy_flag = (
            torch.linalg.norm(offset[..., :2], axis=1)
            <= self.pad_half_size[0] - self.cube_half_size[0]
        )
        z_flag = (
            torch.abs(offset[..., 2] - self.cube_half_size[2] - self.pad_half_size[2])
            <= 0.005
        )
        is_cube_on_pad = torch.logical_and(xy_flag, z_flag)
        is_cube_static = self.cube.is_static(lin_thresh=1e-2, ang_thresh=0.5)
        is_cube_grasped = self.agent.is_grasping(self.cube)
        success = is_cube_on_pad & is_cube_static & (~is_cube_grasped)
        return {
            "is_cube_grasped": is_cube_grasped,
            "is_cube_on_pad": is_cube_on_pad,
            "is_cube_static": is_cube_static,
            "success": success,
        }

    def _get_obs_extra(self, info: dict):
        obs = dict(
            tcp_pose=self.agent.tcp.pose.raw_pose,
            pad_pos=self.pad.pose.p,
        )
        if "state" in self.obs_mode:
            obs.update(
                cube_pose=self.cube.pose.raw_pose,
                tcp_to_cube_pos=self.cube.pose.p - self.agent.tcp.pose.p,
                cube_to_pad_pos=self.pad.pose.p - self.cube.pose.p,
            )
        return obs
