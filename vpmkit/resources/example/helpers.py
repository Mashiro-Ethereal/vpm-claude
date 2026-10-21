# Helpers that evaluate() in env_source.py calls, and how a candidate uses each.
# This is the example task's copy; a real input package has the same format and
# lists only the helpers its own evaluate() calls.

# ---------------------------------------------------------------------------
# self.agent.is_grasping(self.cube)
#   Panda.is_grasping (mani_skill/agents/robots/panda/panda.py)
#   Use the adapter reading w.grasping(g, o): it calls this method with its
#   default arguments (min_force=0.5, max_angle=85), as evaluate() does.
#   Source not included.

# ---------------------------------------------------------------------------
# self.cube.is_static(lin_thresh=1e-2, ang_thresh=0.5)
#   Actor.is_static (mani_skill/utils/structs/actor.py)
#   In a candidate, self.linear_velocity and self.angular_velocity are the
#   object view fields o.lin_vel and o.ang_vel.
def is_static(self, lin_thresh=1e-2, ang_thresh=1e-1):
    """
    Checks if this actor is static within the given linear velocity threshold `lin_thresh` and angular velocity threshold `ang_thresh`
    """
    return torch.logical_and(
        torch.linalg.norm(self.linear_velocity, axis=1) <= lin_thresh,
        torch.linalg.norm(self.angular_velocity, axis=1) <= ang_thresh,
    )
