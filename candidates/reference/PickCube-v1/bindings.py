"""Object bindings for PickCube-v1 (reference candidate)."""


def bind(env, api):
    # cube_half_size is the attribute the scene uses to build the cube.
    # The goal is a target point, bound as a site.
    return {
        "g": api.gripper(),
        "cube": api.actor(env.cube, half_size=env.cube_half_size),
        "goal": api.site(lambda env: env.goal_site.pose),
    }
