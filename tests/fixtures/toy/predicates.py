from vpmkit.api import G, predicate


@predicate(desc="Gripper is open", need_true="Open {g}.",
           need_false="Close {g}.", scale=0.08)
def gripper_open(w, g, *, min_width=0.04):
    return g.width - min_width


@predicate(desc="Gripper is near the block", need_true="Move {g} near {block}.",
           need_false="Move {g} away from {block}.", scale=0.2)
def near(w, g, block, *, max_dist=0.1):
    return max_dist - G.dist(g.pos, block.pos)


@predicate(desc="Block is grasped", need_true="Grasp {block} with {g}.",
           need_false="Release {block} from {g}.")
def grasped(w, g, block):
    return w.grasping(g, block)


@predicate(desc="Block is in the region", need_true="Move {block} into {region}.",
           need_false="Move {block} out of {region}.", scale=0.1)
def in_region(w, block, region, *, radius=0.05):
    return radius - G.dist(block.pos, region.pos)
