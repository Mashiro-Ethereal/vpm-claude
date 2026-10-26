"""Final-observation bootstrap selection for PPO."""

from torch import Tensor


def final_bootstrap_mask(done: Tensor, terminated: Tensor, truncated: Tensor,
                         bootstrap_terminations: bool = False) -> Tensor:
    """Select finished episodes whose final observations retain a value."""
    if bootstrap_terminations:
        return done
    return done & truncated & ~terminated
