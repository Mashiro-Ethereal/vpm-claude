"""Binding validation and snapshot reads without simulation."""

from dataclasses import is_dataclass
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch
from mani_skill.utils.structs.actor import Actor
from mani_skill.utils.structs.pose import Pose

from vpmkit.adapters.maniskill import ManiSkillAdapter, make_env
from vpmkit.adapters.maniskill import binding as api
from vpmkit.errors import BindingError, CandidateError


def fake_actor(n: int = 2, collision: bool = True) -> Mock:
    actor = Mock(spec=Actor)
    actor.pose = Pose.create(torch.tensor([[0., 0., 0., 1., 0., 0., 0.]]).repeat(n, 1))
    actor.linear_velocity = torch.zeros(n, 3)
    actor.angular_velocity = torch.zeros(n, 3)
    actor.has_collision_shapes = collision
    return actor


def fake_env(n: int = 2) -> SimpleNamespace:
    robot = Mock()
    robot.get_qpos.return_value = torch.full((n, 9), 0.02)
    robot.get_qvel.return_value = torch.arange(n * 9, dtype=torch.float64).reshape(n, 9)
    robot.get_qlimits.return_value = torch.tensor([0., 0.04]).expand(n, 9, 2)
    agent = Mock(robot=robot, tcp=fake_actor(n))
    agent.is_grasping.return_value = torch.ones(n, dtype=torch.bool)
    task = SimpleNamespace(device=torch.device("cpu"), num_envs=n, robot_uids="panda",
                           agent=agent, scene=Mock(), cube=fake_actor(n),
                           evaluate=Mock(return_value={"success": torch.ones(n, dtype=torch.bool)}))
    task.scene.get_pairwise_contact_forces.return_value = torch.zeros(n, 3)
    return SimpleNamespace(unwrapped=task)


class BindingTest(unittest.TestCase):
    def test_specs_and_half_sizes(self) -> None:
        actor = fake_actor()
        for value in (0.02, [0.01, 0.02, 0.03], (1, 2, 3), np.ones(3),
                      torch.tensor(0.02), torch.ones(3), torch.ones(1, 3), torch.ones(2, 3)):
            with self.subTest(value=type(value).__name__):
                spec = api.actor(actor, value)
                self.assertTrue(is_dataclass(spec))
                normalized = api.normalize_half_size(spec.half_size, 2, torch.device("cpu"))
                self.assertEqual(normalized.shape, (2, 3))
                self.assertEqual(normalized.dtype, torch.float32)
                torch.testing.assert_close(normalized, torch.as_tensor(value).float().expand(2, 3))
                if isinstance(value, torch.Tensor):
                    self.assertNotEqual(normalized.data_ptr(), value.data_ptr())
        self.assertTrue(is_dataclass(api.gripper()))
        self.assertEqual(api.site(lambda env: env.cube.pose).half_size, 0.)
        api.actor(actor, lambda env: env.size)
        api.gripper(threshold=0.2, vector=[1, 2], array=np.ones(3), dynamic=lambda env: env.value)

    def test_invalid_specs(self) -> None:
        with self.assertRaisesRegex(TypeError, "mani_skill.*Actor"):
            api.actor(object(), 0.02)
        for value in ("0.02", {"x": 1}, [1, "x", 3], 1j):
            with self.subTest(value=value), self.assertRaisesRegex(TypeError, "half_size"):
                api.actor(fake_actor(), value)
        for value in ([1, 2], torch.ones(2, 2), torch.ones(1, 1, 3), np.ones((2, 3))):
            with self.subTest(value=type(value).__name__), self.assertRaisesRegex(ValueError, "half_size"):
                api.site(lambda env: env.pose, half_size=value)
        with self.assertRaisesRegex(ValueError, "broadcast"):
            api.normalize_half_size(torch.ones(4, 3), 2, torch.device("cpu"))
        for value in (torch.zeros(2, 7), None):
            with self.assertRaisesRegex(TypeError, "site pose.*callable"):
                api.site(value)
        for value in (lambda: None, lambda env, extra: None):
            with self.assertRaisesRegex(TypeError, "accept env"):
                api.site(value)
            with self.assertRaisesRegex(TypeError, "half_size"):
                api.actor(fake_actor(), value)
            with self.assertRaisesRegex(TypeError, "attribute"):
                api.gripper(reading=value)
        with self.assertRaisesRegex(TypeError, "numeric"):
            api.gripper(reading="text")

    def test_attribute_names(self) -> None:
        for name in ("pos", "quat", "pose", "lin_vel", "ang_vel", "half_size", "width",
                     "max_width", "arm_qvel", "joint_pos", "joint_vel", "joint_limits", "name", "_private"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "attribute"):
                api.gripper(**{name: 1.})

    def test_factory_defaults_and_overrides(self) -> None:
        with patch("vpmkit.adapters.maniskill.env.gym.make") as make:
            make_env("PickCube-v1", num_envs=8)
            make.assert_called_once_with("PickCube-v1", num_envs=8, sim_backend="physx_cuda",
                                         obs_mode="state", reward_mode="sparse", render_mode=None)
            make.reset_mock()
            make_env("PickCube-v1", obs_mode="none", control_mode="pd_ee_delta_pos")
            make.assert_called_once_with("PickCube-v1", num_envs=1, sim_backend="physx_cpu",
                                         obs_mode="none", reward_mode="sparse", render_mode=None,
                                         control_mode="pd_ee_delta_pos")

    def test_broadcasting(self) -> None:
        for value, shape in ((2, (2,)), ([1, 2], (2,)), ([1, 2, 3], (2, 3)),
                             (torch.ones(1, 2), (2, 2)), (torch.ones(2, 7), (2, 7)),
                             (fake_actor().pose, (2, 7))):
            with self.subTest(shape=shape):
                result = api.broadcast_reading(value, 2, torch.device("cpu"))
                self.assertEqual(result.shape, shape)
                self.assertEqual(result.dtype, torch.float32)


class AdapterTest(unittest.TestCase):
    def test_bind_errors_and_robot_support(self) -> None:
        env = fake_env()
        original = RuntimeError("candidate failure")
        with self.assertRaisesRegex(BindingError, "bind.*candidate failure") as error:
            ManiSkillAdapter(env, Mock(side_effect=original))
        self.assertIs(error.exception.__cause__, original)
        self.assertIsInstance(error.exception, CandidateError)
        for result, key in (([], "bind"), ({1: api.gripper()}, "bind"),
                            ({"cube": object()}, "cube"),
                            ({"g": api.gripper(), "other": api.gripper()}, "bind")):
            with self.subTest(key=key), self.assertRaises(BindingError) as error:
                ManiSkillAdapter(env, lambda env, api: result)
            self.assertEqual(error.exception.key, key)
            self.assertIsNotNone(error.exception.__cause__)
        env.unwrapped.robot_uids = "panda_wristcam"
        ManiSkillAdapter(env, lambda env, api: {"g": api.gripper()}).snapshot()
        env.unwrapped.robot_uids = "fetch"
        with self.assertRaisesRegex(NotImplementedError, "fetch"):
            ManiSkillAdapter(env, lambda env, api: {"g": api.gripper()})

    def test_snapshot_values_callables_and_copies(self) -> None:
        env = fake_env()
        task = env.unwrapped
        size = torch.ones(2, 3, dtype=torch.float64)
        dynamic = Mock(side_effect=lambda env: env.cube.pose)
        bind = Mock(side_effect=lambda env, api: {
            "g": api.gripper(),
            "cube": api.actor(env.cube, lambda env: size, offset=[1., 2., 3.], frame=dynamic),
            "goal": api.site(lambda env: env.cube.pose, threshold=0.025),
        })
        adapter = ManiSkillAdapter(env, bind)
        bind.assert_called_once_with(task, api)
        before = adapter.snapshot()
        saved = {name: tensor.clone() for name, tensor in before._tensor_items()}
        body = before.bodies["g"]
        torch.testing.assert_close(body.width, torch.full((2,), 0.04))
        torch.testing.assert_close(body.max_width, torch.full((2,), 0.08))
        torch.testing.assert_close(body.arm_qvel, task.agent.robot.get_qvel()[:, :-2].float())
        self.assertEqual(body.arm_qvel.shape, (2, 7))
        self.assertEqual(before.bodies["cube"].attrs["frame"].shape, (2, 7))
        self.assertEqual(before.bodies["cube"].attrs["offset"].shape, (2, 3))
        for name, tensor in before._tensor_items():
            self.assertEqual(tensor.dtype, torch.bool if name.startswith("grasping") else torch.float32)
        task.cube.pose.raw_pose.add_(1)
        task.cube.linear_velocity.add_(1)
        task.agent.robot.get_qvel.return_value.add_(1)
        task.evaluate.return_value["success"].fill_(False)
        size.mul_(2)
        after = adapter.snapshot()
        for name, tensor in before._tensor_items():
            torch.testing.assert_close(tensor, saved[name])
        self.assertEqual(dynamic.call_count, 2)
        dynamic.assert_called_with(task)
        torch.testing.assert_close(after.bodies["cube"].half_size, torch.full((2, 3), 2.))
        torch.testing.assert_close(after.bodies["goal"].lin_vel, torch.zeros(2, 3))
        self.assertEqual(set(before.grasping), {("g", "cube")})
        self.assertEqual(set(before.contact_force), {("g", "cube")})

    def test_official_keys_and_info(self) -> None:
        env = fake_env()
        task = env.unwrapped
        adapter = ManiSkillAdapter(env, lambda env, api: {})
        info = {"success": torch.zeros(2), "elapsed_steps": torch.ones(2)}
        self.assertEqual(set(adapter.snapshot(info).official), {"success"})
        task.evaluate.assert_called_once_with()
        task.evaluate.reset_mock()
        torch.testing.assert_close(adapter.snapshot(info).official["success"], info["success"])
        task.evaluate.assert_not_called()
        adapter.snapshot()
        task.evaluate.assert_called_once_with()

    def test_contacts_and_visual_only_actor(self) -> None:
        env = fake_env()
        task = env.unwrapped
        other, visual = fake_actor(), fake_actor(collision=False)
        def forces(a, b):
            self.assertIsNot(a, visual)
            self.assertIsNot(b, visual)
            vector = ([3., 4., 0.] if a is task.agent.finger1_link else
                      [-3., -4., 0.] if a is task.agent.finger2_link else [0., 0., 12.])
            return torch.tensor([vector]).expand(2, 3)
        task.scene.get_pairwise_contact_forces.side_effect = forces
        adapter = ManiSkillAdapter(env, lambda env, api: {
            "cube": api.actor(env.cube, 0.02), "g": api.gripper(),
            "other": api.actor(other, 0.03), "visual": api.actor(visual, 0.01),
        })
        snap = adapter.snapshot()
        self.assertEqual(len(snap.contact_force), 6)
        torch.testing.assert_close(snap.contact_force[("cube", "g")], torch.full((2,), 10.))
        torch.testing.assert_close(snap.contact_force[("cube", "other")], torch.full((2,), 12.))
        for pair, force in snap.contact_force.items():
            if "visual" in pair:
                self.assertFalse(force.any())
        self.assertFalse(snap.grasping[("g", "visual")].any())
        self.assertEqual(task.agent.is_grasping.call_count, 2)
        self.assertTrue(all(call.args[0] is not visual for call in task.agent.is_grasping.call_args_list))

    def test_read_errors_name_binding_and_chain(self) -> None:
        env = fake_env()
        original = RuntimeError("unreadable")
        for spec in (api.site(Mock(side_effect=original)),
                     api.actor(env.unwrapped.cube, Mock(side_effect=original)),
                     api.gripper(reading=Mock(side_effect=original)),
                     api.site(lambda env: torch.ones(2, 6)),
                     api.actor(env.unwrapped.cube, lambda env: [1, 2]),
                     api.gripper(reading=lambda env: "invalid")):
            with self.subTest(spec=type(spec).__name__):
                adapter = ManiSkillAdapter(env, lambda env, api: {"broken": spec})
                with self.assertRaisesRegex(BindingError, "broken") as error:
                    adapter.snapshot()
                self.assertIsNotNone(error.exception.__cause__)
        adapter = ManiSkillAdapter(env, lambda env, api: {
            "g": api.gripper(), "cube": api.actor(env.cube, 0.02)})
        env.unwrapped.agent.is_grasping.side_effect = original
        with self.assertRaisesRegex(BindingError, "cube") as error:
            adapter.snapshot()
        self.assertIs(error.exception.__cause__, original)
        env.unwrapped.agent.is_grasping.side_effect = None
        env.unwrapped.scene.get_pairwise_contact_forces.side_effect = original
        with self.assertRaisesRegex(BindingError, "g, cube") as error:
            adapter.snapshot()
        self.assertIs(error.exception.__cause__, original)
