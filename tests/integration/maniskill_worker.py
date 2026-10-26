"""Run one ManiSkill environment and print its test results as JSON."""

import json
from pathlib import Path
import sys
from typing import Any
from unittest.mock import patch

import torch

from vpmkit.adapters.maniskill import ManiSkillAdapter, make_env, scene_inventory
from vpmkit.world import Snapshot, make_views


def bind(env: Any, api: Any) -> dict:
    return {"g": api.gripper(), "cube": api.actor(env.cube, half_size=env.cube_half_size),
            "goal": api.site(lambda env: env.goal_site.pose)}


def check_state(snapshot: Snapshot, task: Any, n: int, device: str) -> None:
    snapshot.__post_init__()
    assert snapshot.batch_size == n
    assert snapshot.device.type == device
    world, _, objects = make_views(snapshot)
    g, cube, goal = objects.g, objects.cube, objects.goal
    for body in snapshot.bodies.values():
        assert body.pose.shape == (n, 7)
        assert body.lin_vel.shape == body.ang_vel.shape == (n, 3)
    assert g.width.shape == g.max_width.shape == (n,)
    assert g.arm_qvel.shape == (n, 7)
    assert cube.half_size.shape == goal.half_size.shape == (n, 3)
    torch.testing.assert_close(cube.half_size, torch.full((n, 3), 0.02, device=task.device))
    torch.testing.assert_close(snapshot.table_z, torch.zeros(n, device=task.device))
    torch.testing.assert_close(g.pose, task.agent.tcp.pose.raw_pose)
    torch.testing.assert_close(g.lin_vel, task.agent.tcp.linear_velocity)
    torch.testing.assert_close(g.ang_vel, task.agent.tcp.angular_velocity)
    torch.testing.assert_close(goal.pose, task.goal_site.pose.raw_pose)
    torch.testing.assert_close(goal.lin_vel, torch.zeros(n, 3, device=task.device))
    torch.testing.assert_close(goal.ang_vel, torch.zeros(n, 3, device=task.device))
    torch.testing.assert_close(cube.pose, task.cube.pose.raw_pose)
    torch.testing.assert_close(cube.lin_vel, task.cube.linear_velocity)
    torch.testing.assert_close(cube.ang_vel, task.cube.angular_velocity)
    torch.testing.assert_close(g.arm_qvel, task.agent.robot.get_qvel()[:, :-2])
    torch.testing.assert_close(g.width, task.agent.robot.get_qpos()[:, -2:].sum(-1))
    torch.testing.assert_close(g.max_width, task.agent.robot.get_qlimits()[:, -2:, 1].sum(-1))
    assert torch.all(g.width >= 0)
    assert torch.all(g.width <= g.max_width + 1e-4)
    torch.testing.assert_close(g.max_width, torch.full((n,), 0.08, device=task.device))
    assert torch.equal(world.grasping(g, cube), task.agent.is_grasping(task.cube))
    assert set(snapshot.grasping) == {("g", "cube")}
    assert set(snapshot.contact_force) == {("g", "cube")}
    force = world.contact_force(g, cube)
    assert torch.all(torch.isfinite(force) & (force >= 0))
    query = task.scene.get_pairwise_contact_forces
    expected_force = (query(task.agent.finger1_link, task.cube).norm(dim=-1)
                      + query(task.agent.finger2_link, task.cube).norm(dim=-1))
    torch.testing.assert_close(force, expected_force)
    torch.testing.assert_close(world.contact_force(cube, g), force)
    official = task.evaluate()
    assert set(snapshot.official) == set(official) == {"success", "is_obj_placed", "is_robot_static", "is_grasped"}
    for key, value in official.items():
        torch.testing.assert_close(snapshot.official[key], value.float())
    for name, tensor in snapshot._tensor_items():
        assert tensor.device.type == device
        assert tensor.dtype == (torch.bool if name.startswith("grasping") else torch.float32)


def table_evidence(task: Any) -> dict:
    table = task.table_scene.table
    local = table.get_collision_meshes(to_world_frame=False)
    world = table.get_collision_meshes(to_world_frame=True)
    tops = [float(mesh.bounds[1, 2]) for mesh in world]
    assert all(abs(top) < 1e-6 for top in tops), tops
    return {"actor": table.name, "pose_z": table.pose.p[:, 2].tolist(),
            "local_z_bounds": local[0].bounds[:, 2].tolist(), "world_top_z": tops,
            "table_height": float(task.table_scene.table_height)}


def check_hidden_and_actor_contacts(env: Any) -> None:
    task = env.unwrapped
    expected_pose = task.goal_site.pose.raw_pose.clone()
    task.goal_site.hide_visual()
    adapter = ManiSkillAdapter(env, lambda env, api: {
        **bind(env, api),
        "visual": api.actor(env.goal_site, env.goal_thresh),
        "table": api.actor(env.table_scene.table, [1., 1., 1.]),
    })
    query = task.scene.get_pairwise_contact_forces
    grasp = task.agent.is_grasping
    def checked_query(a, b):
        assert a is not task.goal_site and b is not task.goal_site
        return query(a, b)
    def checked_grasp(actor):
        assert actor is not task.goal_site
        return grasp(actor)
    with patch.object(task.scene, "get_pairwise_contact_forces", side_effect=checked_query), \
            patch.object(task.agent, "is_grasping", side_effect=checked_grasp):
        snapshot = adapter.snapshot()
    torch.testing.assert_close(snapshot.bodies["visual"].pose, expected_pose)
    torch.testing.assert_close(snapshot.bodies["goal"].pose, expected_pose)
    assert not snapshot.grasping[("g", "visual")].any()
    for pair, value in snapshot.contact_force.items():
        if "visual" in pair:
            assert not value.any()
    torch.testing.assert_close(snapshot.contact_force[("cube", "table")],
                               query(task.cube, task.table_scene.table).norm(dim=-1))


def snapshots(num_envs: int) -> dict:
    env = make_env("PickCube-v1", num_envs=num_envs)
    try:
        _, info = env.reset(seed=0)
        task = env.unwrapped
        adapter = ManiSkillAdapter(env, bind)
        snapshot = adapter.snapshot(info)
        torch.testing.assert_close(snapshot.bodies["cube"].pose[:, 2],
                                   torch.full((num_envs,), 0.02, device=task.device), rtol=0, atol=1e-3)
        device = "cuda" if num_envs > 1 else "cpu"
        check_state(snapshot, task, num_envs, device)
        evidence = table_evidence(task)
        env.action_space.seed(0)
        for step in range(10):
            saved = {name: value.clone() for name, value in snapshot._tensor_items()}
            _, _, _, _, info = env.step(env.action_space.sample())
            for name, value in snapshot._tensor_items():
                torch.testing.assert_close(value, saved[name], rtol=0, atol=0)
            snapshot = adapter.snapshot(info if step % 2 == 0 else None)
            check_state(snapshot, task, num_envs, device)
        check_hidden_and_actor_contacts(env)
        return {"device": device, "num_envs": num_envs, "states": 11,
                "unchanged_after_step": True, "hidden_actor_checked": True, "table": evidence}
    finally:
        env.close()


def scripted_grasp() -> dict:
    env = make_env("PickCube-v1", num_envs=1, control_mode="pd_ee_delta_pos",
                   robot_init_qpos_noise=0.0, max_episode_steps=120)
    try:
        env.reset(seed=0)
        task = env.unwrapped
        adapter = ManiSkillAdapter(env, bind)
        first_grasp = None
        grasped_steps = 0
        steps = 0
        cube_xy = task.cube.pose.p[0, :2].clone()
        start = task.agent.tcp.pose.p[0].clone()
        above = torch.cat([cube_xy, torch.tensor([0.14])])
        down = torch.cat([cube_xy, torch.tensor([0.025])])
        phases = [(start, 1., 5), (above, 1., 20), (down, 1., 25), (down, -1., 20)]
        initial = adapter.snapshot()
        assert torch.equal(initial.grasping[("g", "cube")], task.agent.is_grasping(task.cube))
        for target, opening, count in phases:
            for _ in range(count):
                delta = ((target - task.agent.tcp.pose.p[0]) / 0.1).clamp(-0.4, 0.4)
                action = torch.cat([delta, torch.tensor([opening])]).unsqueeze(0)
                _, _, _, _, info = env.step(action)
                steps += 1
                snapshot = adapter.snapshot(info)
                world, _, objects = make_views(snapshot)
                official = task.agent.is_grasping(task.cube)
                assert torch.equal(world.grasping(objects.g, objects.cube), official)
                if official.item():
                    assert world.contact_force(objects.g, objects.cube).item() > 0
                    grasped_steps += 1
                    if first_grasp is None:
                        first_grasp = steps
        return {"first_grasp_step": first_grasp, "grasped_steps": grasped_steps,
                "steps": steps, "final_tcp": task.agent.tcp.pose.p.tolist(),
                "final_cube": task.cube.pose.p.tolist()}
    finally:
        env.close()


def inventory() -> dict:
    markdown = scene_inventory("PickCube-v1")
    path = Path(__file__).resolve().parents[2] / "outputs/stage1/m2/scene_inventory_PickCube-v1.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return {"markdown": markdown, "path": str(path)}


if __name__ == "__main__":
    mode = sys.argv[1]
    result = {"gpu": lambda: snapshots(8), "cpu": lambda: snapshots(1),
              "grasp": scripted_grasp, "inventory": inventory}[mode]()
    print(json.dumps(result))
