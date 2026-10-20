"""Run with CUDA_VISIBLE_DEVICES=0 VPM_RUN_MANISKILL=1 python -m unittest."""

from itertools import combinations
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import torch

from vpmkit import geometry as G
from vpmkit.adapters import (
    AdapterError, ManiSkillAdapter, MilestoneTracker, inventory_markdown,
    make_env, random_rollout, scene_inventory,
)
from vpmkit.world import ObjSpec


def bind_task(env, api):
    bindings = {"g": api.gripper(), "table": api.table()}
    task = env.spec.id
    if task == "PushCube-v1":
        bindings["cube"] = api.actor(env.obj, env.cube_half_size)
        bindings["goal"] = api.site(env.goal_region)
    elif task == "PickCube-v1":
        bindings["cube"] = api.actor(env.cube, [env.cube_half_size] * 3)
        bindings["goal"] = api.site(env.goal_site)
    elif task == "LiftPegUpright-v1":
        bindings["peg"] = api.actor(env.peg, [env.peg_half_length, env.peg_half_width, env.peg_half_width])
    elif task == "PegInsertionSide-v1":
        bindings["peg"] = api.actor(env.peg, lambda: env.peg_half_sizes,
                                    attrs={"head_offset": lambda: env.peg_head_offsets.p})
        bindings["box"] = api.actor(env.box, lambda: env.peg_half_sizes[:, :1].expand(-1, 3), attrs={
            "hole_offset": lambda: env.box_hole_offsets.p,
            "hole_radius": lambda: env.box_hole_radii,
        })
        bindings["hole"] = api.site(lambda: env.box_hole_pose)
    else:
        bindings["a"] = api.actor(env.cubeA, env.cube_half_size)
        bindings["b"] = api.actor(env.cubeB, env.cube_half_size)
        if task == "StackPyramid-v1":
            bindings["c"] = api.actor(env.cubeC, env.cube_half_size)
    return bindings


@unittest.skipUnless(os.environ.get("VPM_RUN_MANISKILL") == "1", "set VPM_RUN_MANISKILL=1")
class ManiSkillAdapterTests(unittest.TestCase):
    def assert_world(self, world, env, adapter):
        base = env.unwrapped
        tensor_device = base.agent.tcp.pose.p.device
        world.validate()
        self.assertEqual(world.N, base.num_envs)
        self.assertEqual(world.device, base.device)
        self.assertEqual(world.meta, {"env_id": base.spec.id, "num_envs": base.num_envs})
        official = base.evaluate()
        self.assertEqual(world.official.keys(), official.keys())
        for key, value in official.items():
            expected = torch.as_tensor(value, device=base.device)
            expected = expected.to(torch.bool if expected.dtype == torch.bool else torch.float32)
            torch.testing.assert_close(world.official[key], expected)
        actors = [h for h, s in adapter.bindings.items() if s.kind == "actor"]
        self.assertEqual(set(world.grasping), {("g", a) for a in actors})
        self.assertEqual(set(world.contacts), set(combinations(actors, 2)))
        for handle, obj in world.objects.items():
            for field in ("pos", "quat", "linvel", "angvel", "half_size"):
                tensor = getattr(obj, field)
                self.assertEqual(tensor.shape, (world.N, 4 if field == "quat" else 3))
                self.assertEqual(tensor.dtype, torch.float32)
                self.assertTrue(torch.isfinite(tensor).all())
            for tensor in obj.attrs.values():
                self.assertEqual(tensor.shape[0], world.N)
                self.assertEqual(tensor.device, tensor_device)
                self.assertTrue(torch.isfinite(tensor).all())
            if obj.kind == "actor":
                source = adapter.bindings[handle].source
                source = (base.scene.actor_views if source.merged else base.scene.actors)[source.name]
                torch.testing.assert_close(obj.pos, source.pose.p)
                torch.testing.assert_close(obj.quat, source.pose.q)
                torch.testing.assert_close(world.grasping["g", handle], base.agent.is_grasping(source))
                if source.px_body_type == "dynamic":
                    torch.testing.assert_close(obj.linvel, source.linear_velocity)
                    torch.testing.assert_close(obj.angvel, source.angular_velocity)
            if obj.kind in {"site", "table"}:
                self.assertFalse(obj.linvel.any())
                self.assertFalse(obj.angvel.any())
        for values in (world.contacts, world.official):
            for tensor in values.values():
                self.assertTrue(torch.isfinite(tensor).all())
        g = world.objects["g"]
        torch.testing.assert_close(g.pos, base.agent.tcp.pose.p)
        torch.testing.assert_close(g.quat, base.agent.tcp.pose.q)
        torch.testing.assert_close(g.linvel, base.agent.tcp.linear_velocity)
        torch.testing.assert_close(g.angvel, base.agent.tcp.angular_velocity)
        torch.testing.assert_close(g.attrs["width"], base.agent.robot.get_qpos()[:, -2:].sum(-1))
        torch.testing.assert_close(g.attrs["arm_qvel"], base.agent.robot.get_qvel()[:, :-2])
        self.assertTrue(((g.attrs["width"] >= 0) & (g.attrs["width"] <= 0.09)).all())
        table = world.objects["table"]
        torch.testing.assert_close(table.pos[:, 2] + table.half_size[:, 2], torch.zeros(world.N, device=base.device))

    def assert_milestones(self, tracker, base):
        readings = tracker.read()
        tensor_device = base.agent.tcp.pose.p.device
        dynamic = [a for a in base.scene.actors.values() if a.px_body_type == "dynamic"]
        expected = {f"official:{k}" for k, v in base.evaluate().items() if torch.as_tensor(v).dtype == torch.bool}
        expected.update(f"{kind}:{a.name}" for a in dynamic for kind in ("grasped", "lifted"))
        self.assertEqual(set(readings), expected)
        for value in readings.values():
            self.assertEqual(value.shape, (base.num_envs,))
            self.assertEqual(value.dtype, torch.bool)
            self.assertEqual(value.device, tensor_device)
        return readings

    def check_task(self, env_id):
        env = make_env(env_id, num_envs=4, seed=7)
        try:
            base = env.unwrapped
            self.assertEqual(base.device.type, "cuda")
            bind_calls = []

            def bind(e, api):
                bind_calls.append(e)
                return bind_task(e, api)

            adapter = ManiSkillAdapter(env, bind)
            tracker = MilestoneTracker(env)
            readings = self.assert_milestones(tracker, base)
            self.assertFalse(any(v.any() for k, v in readings.items() if k.startswith("lifted:")))
            self.assert_world(adapter.snapshot(), env, adapter)
            frames = random_rollout(env, adapter, steps=5, seed=11)
            self.assertEqual(len(frames), 6)
            for frame in frames:
                frame.validate()
            self.assert_world(frames[-1], env, adapter)
            self.assertEqual(bind_calls, [base])
            saved_pos = frames[-1].objects["g"].pos.clone()
            env.step(env.action_space.sample())
            torch.testing.assert_close(frames[-1].objects["g"].pos, saved_pos)
            self.assert_milestones(tracker, base)

            if env_id == "LiftPegUpright-v1":
                self.assert_euler(base.peg.pose.q)
            if env_id == "PegInsertionSide-v1":
                world = adapter.snapshot()
                torch.testing.assert_close(world.objects["peg"].attrs["head_offset"], base.peg_head_offsets.p)
                torch.testing.assert_close(world.objects["box"].attrs["hole_offset"], base.box_hole_offsets.p)
                torch.testing.assert_close(world.objects["box"].attrs["hole_radius"], base.box_hole_radii)
                flags = torch.tensor([True, False, True, False], device=base.device)
                with patch.object(base.agent, "is_grasping", return_value=flags) as query:
                    readings = tracker.read()
                    for i in range(4):
                        expected = torch.zeros_like(flags)
                        expected[i] = flags[i]
                        torch.testing.assert_close(readings[f"grasped:peg_{i}"], expected)
                    self.assertTrue(all(call.args[0] is base.peg for call in query.call_args_list))

            # Move actors through the public state API to exercise positive lift
            # readings and independent reset baselines, without a grasp policy.
            tracker.reset()
            state = base.get_state_dict()
            for key, value in state["actors"].items():
                if key in {a.name for a in tracker.actors.values()} or key == "peg":
                    value[:, 2] += 0.05
            base.set_state_dict(state)
            readings = tracker.read()
            for actor in tracker.actors.values():
                self.assertTrue(readings[f"lifted:{actor.name}"][actor._scene_idxs.long()].all())
            env.reset(options={"env_idx": torch.tensor([0], device=base.device)})
            tracker.reset(env_idx=torch.tensor([0], device=base.device))
            readings = tracker.read()
            for actor in tracker.actors.values():
                lifted = readings[f"lifted:{actor.name}"]
                self.assertFalse(lifted[0])
                idx = actor._scene_idxs.long()
                self.assertTrue(lifted[idx[idx != 0]].all())
            actor_names = set(base.scene.actors)
        finally:
            env.close()

        inventory = scene_inventory(env_id)
        json.dumps(inventory, allow_nan=False)
        if env_id == "PegInsertionSide-v1":
            actor_names = {"table-workspace", "ground", "peg_0", "box_with_hole_0"}
        self.assertEqual({a["name"] for a in inventory["actors"]}, actor_names)
        self.assertEqual(inventory["seeds"], [0, 1, 2, 3, 4])
        for actor in inventory["actors"]:
            self.assertEqual(len(actor["position_min"]), 3)
            self.assertTrue(all(a <= b for a, b in zip(actor["position_min"], actor["position_max"])))
            self.assertLessEqual(*actor["yaw_range"])
        self.assertIn("success", inventory["evaluate"])
        self.assertTrue(inventory["agent"]["control_mode"])
        numeric = inventory["numeric_attributes"]
        if env_id == "PegInsertionSide-v1":
            self.assertEqual(numeric["peg_half_sizes"]["shape"], [1, 3])
        elif env_id == "LiftPegUpright-v1":
            self.assertEqual(numeric["peg_half_length"], 0.12)
        else:
            self.assertIn("cube_half_size", numeric)
        markdown = inventory_markdown(inventory)
        self.assertIn(env_id, markdown)
        for actor in inventory["actors"]:
            self.assertIn(actor["name"], markdown)

    def assert_euler(self, q):
        from mani_skill.utils.geometry import rotation_conversions as rotations
        expected = rotations.matrix_to_euler_angles(rotations.quaternion_to_matrix(q), "XYZ")
        torch.testing.assert_close(G.quat_to_euler_xyz(q), expected, atol=1e-5, rtol=0)

    def run_task(self, env_id):
        # SAPIEN 3.0.3 can crash when repeatedly replacing GPU scenes for
        # different tasks in one process. Each task still tests four live rows.
        result = subprocess.run([
            sys.executable, "-c",
            "import sys; from tests.integration.test_maniskill_adapter import ManiSkillAdapterTests; "
            "ManiSkillAdapterTests().check_task(sys.argv[1])",
            env_id,
        ], capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_push_cube(self):
        self.run_task("PushCube-v1")

    def test_pick_cube(self):
        self.run_task("PickCube-v1")

    def test_lift_peg_upright(self):
        self.run_task("LiftPegUpright-v1")

    def test_stack_cube(self):
        self.run_task("StackCube-v1")

    def test_peg_insertion_side(self):
        self.run_task("PegInsertionSide-v1")

    def test_stack_pyramid(self):
        self.run_task("StackPyramid-v1")

    def test_geometry(self):
        generator = torch.Generator().manual_seed(42)
        q = torch.randn(256, 4, generator=generator, device="cpu").to("cuda:0")
        self.assert_euler(G.quat_normalize(q))
        self.assert_euler(q * 3)

    def test_cpu_bindings_and_reconfiguration(self):
        env = make_env("PegInsertionSide-v1", seed=2)
        try:
            base = env.unwrapped
            self.assertEqual(base.device.type, "cpu")
            calls = []

            def bind(e, api):
                calls.append(e)
                bindings = bind_task(e, api)
                bindings["ground"] = api.actor(e.scene.actors["ground"], 1.0)
                bindings["peg"].attrs["constant"] = 0.25
                return bindings

            adapter = ManiSkillAdapter(env, bind)
            old = adapter.snapshot()
            old_offset = old.objects["peg"].attrs["head_offset"].clone()
            env.reset(seed=3)
            current = adapter.snapshot()
            self.assert_world(current, env, adapter)
            torch.testing.assert_close(old.objects["peg"].attrs["head_offset"], old_offset)
            self.assertFalse(torch.equal(old_offset, current.objects["peg"].attrs["head_offset"]))
            torch.testing.assert_close(current.objects["peg"].half_size, base.peg_half_sizes)
            torch.testing.assert_close(current.objects["hole"].pos, base.box_hole_pose.p)
            self.assertEqual(current.objects["peg"].attrs["constant"].tolist(), [0.25])
            self.assertFalse(current.objects["ground"].linvel.any())
            self.assertFalse(current.objects["ground"].angvel.any())
            self.assertEqual(calls, [base])
            for invalid, message in (
                ([], "dict"), ({"x": 1}, "ObjSpec"),
                ({"x": ObjSpec("unknown", None)}, "unknown kind"),
                ({"x": ObjSpec("actor", base.peg, [1, 2])}, "x.half_size.*shape"),
                ({"x": ObjSpec("actor", base.peg, [[1], [2]])}, "x.half_size.*shape"),
                ({"x": ObjSpec("actor", base.peg, 0.1, {"bad": torch.zeros(2, 3)})}, "attrs.*shape"),
            ):
                with self.subTest(message=message), self.assertRaisesRegex(AdapterError, message):
                    ManiSkillAdapter(env, lambda e, api: invalid)
        finally:
            env.close()

        # Inventory/CPU use must not prevent a later batched GPU environment.
        env = make_env("PegInsertionSide-v1", num_envs=4, seed=4)
        try:
            adapter = ManiSkillAdapter(env, bind_task)
            self.assert_world(adapter.snapshot(), env, adapter)
        finally:
            env.close()


if __name__ == "__main__":
    unittest.main()
