"""Temporary copies of the PickCube reference candidate."""

from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
from typing import Iterator

from .mutations import Edit


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "candidates/reference/PickCube-v1"
NEAR_RETURN = "return radius + max_dist - tcp_dist(w, g, o)"
GRASP_RETURN = "return signed(w.grasping(g, o))"


@contextmanager
def reference_copy(*edits: Edit) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="reference-") as folder:
        path = Path(folder) / "candidate"
        shutil.copytree(REFERENCE, path)
        for edit in edits:
            edit.apply(path)
        yield path
