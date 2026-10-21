"""Progress functions for PlaceCubeOnPad-v1 (example).

Only reach has its own progress. grasp has a boolean guard and gets none;
carry and release use the default progress of their guard literals.
"""
from .predicates import tcp_dist


def progress_reach(w, o, d0=0.3):
    # 1 at the cube's center, 0 at d0 or farther. d0 is a fixed scale declared
    # in params, not the distance at which the stage began.
    return 1.0 - tcp_dist(w, o.g, o.cube) / d0
