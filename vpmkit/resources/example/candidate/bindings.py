"""Object bindings for PlaceCubeOnPad-v1 (example)."""


def bind(env, api):
    # The half sizes are the attributes evaluate() reads, so the rewritten
    # `on` uses the official values.
    return {
        "g": api.gripper(),
        "cube": api.actor(env.cube, half_size=env.cube_half_size),
        "pad": api.actor(env.pad, half_size=env.pad_half_size),
    }
