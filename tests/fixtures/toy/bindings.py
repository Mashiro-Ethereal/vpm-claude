from vpmkit.api import BindingAPI


def bind(env, api: BindingAPI):
    return {
        "g": api.gripper(),
        "block": api.actor(env.block, half_size=[0.02, 0.02, 0.02]),
        "region": api.site(lambda: env.region_pose),
    }
