"""CPU-only fixtures for the simulator-independent M1 core."""

from pathlib import Path

import torch

from vpmkit.world import ObjState, WorldState


ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "tests" / "fixtures" / "toy"


def world(n=1, *, g_x=0.0, block_x=0.2, region_x=1.0, width=0.08, held=False):
    def batch(value, dtype=torch.float32):
        return torch.as_tensor(value, dtype=dtype).expand(n).clone()

    def obj(x, kind, attrs=None):
        pos = torch.zeros(n, 3)
        pos[:, 0] = batch(x)
        return ObjState(pos, torch.tensor([1., 0., 0., 0.]).expand(n, 4).clone(),
                        torch.zeros(n, 3), torch.zeros(n, 3), torch.full((n, 3), 0.02),
                        kind, attrs or {})

    return WorldState(
        n, "cpu",
        {"g": obj(g_x, "gripper", {"width": batch(width), "arm_qvel": torch.zeros(n, 7)}),
         "block": obj(block_x, "actor"), "region": obj(region_x, "site")},
        {("g", "block"): batch(held, torch.bool)},
        {("g", "block"): batch(2.0)}, {"success": batch(False, torch.bool)},
        {"fixture": "synthetic"},
    )
