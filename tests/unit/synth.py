"""Synthetic snapshots and temporary candidates for runtime tests."""

from contextlib import contextmanager
from pathlib import Path
import tempfile
import textwrap
from typing import Any, Iterator

import torch
from torch import Tensor
import yaml

from vpmkit.candidate import Candidate, load_candidate_unchecked
from vpmkit.world import BodyState, Snapshot


EXAMPLE = Path(__file__).resolve().parents[2] / "vpmkit/resources/example/candidate"


def batch(value: Any, n: int, tail: tuple[int, ...], dtype: torch.dtype = torch.float32) -> Tensor:
    return torch.as_tensor(value, dtype=dtype).expand((n,) + tail).clone()


def pose(position: Any, n: int = 1, quaternion: Any = (1, 0, 0, 0)) -> Tensor:
    return torch.cat((batch(position, n, (3,)), batch(quaternion, n, (4,))), -1)


def snapshot(n: int = 1, tcp: Any = (0, 0, 0.06), cube: Any = (0, 0, 0.02),
             pad: Any = (0.2, 0, 0.005), grasp: Any = False, lin_vel: Any = (0, 0, 0),
             ang_vel: Any = (0, 0, 0), cube_quat: Any = (1, 0, 0, 0),
             pad_quat: Any = (1, 0, 0, 0)) -> Snapshot:
    zeros = torch.zeros(n, 3)
    bodies = {
        "g": BodyState("gripper", pose(tcp, n), zeros.clone(), zeros.clone(), None, {},
                       width=torch.full((n,), 0.04), max_width=torch.full((n,), 0.08),
                       arm_qvel=torch.zeros(n, 7)),
        "cube": BodyState("actor", pose(cube, n, cube_quat), batch(lin_vel, n, (3,)),
                          batch(ang_vel, n, (3,)), torch.full((n, 3), 0.02), {}),
        "pad": BodyState("site", pose(pad, n, pad_quat), zeros.clone(), zeros.clone(),
                         batch((0.06, 0.06, 0.005), n, (3,)), {}),
    }
    return Snapshot(bodies, torch.zeros(n), {("g", "cube"): batch(grasp, n, (), torch.bool)},
                    {("cube", "pad"): torch.zeros(n)}, {"success": torch.zeros(n, dtype=torch.bool)})


def trajectory(n: int = 6, length: int = 12) -> list[Snapshot]:
    """Six interleaved motions exercise success, slipping and moving away."""
    result = []
    for t in range(length):
        phase = (torch.arange(n) + t) % 6
        cube = batch((0, 0, 0.02), n, (3,))
        on_pad = (phase >= 3) & (phase <= 4)
        cube[on_pad] = torch.tensor([0.2, 0, 0.03])
        tcp = cube + torch.tensor([0.0, 0.0, 0.04])
        tcp[(phase == 0) | (phase == 5)] += torch.tensor([0.4, 0.0, 0.0])
        velocity = torch.zeros(n, 3)
        velocity[phase == 4, 0] = 0.015
        result.append(snapshot(n, tcp=tcp, cube=cube, grasp=(phase == 2) | (phase == 3), lin_vel=velocity))
    return result


def graph(stages: list[dict[str, Any]] | None = None, params: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"task": "Test a process teacher.", "objects": {"g": {"name": "the gripper"},
            "cube": {"name": "the red cube"}, "pad": {"name": "the target pad"}},
            "stages": stages if stages is not None else [{"name": "only", "exit": ["p(cube)"]}],
            "official": [], "params": params or []}


DEFAULT_PREDICATES = '''
import torch
from vpmkit.api import predicate, signed

@predicate(desc="Object reading.", need_true="move {o}.", need_false="release {o}.", scale=1)
def p(w, o):
    return o.pos[:, 0]
'''


@contextmanager
def candidate_dir(data: dict[str, Any] | None = None, predicates: str = DEFAULT_PREDICATES,
                  progress: str | None = None, bindings: str | None = None) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)
        (path / "stage_graph.yaml").write_text(yaml.safe_dump(data if data is not None else graph()), encoding="utf-8")
        (path / "predicates.py").write_text(textwrap.dedent(predicates), encoding="utf-8")
        for name, source in (("progress.py", progress), ("bindings.py", bindings)):
            if source is not None:
                (path / name).write_text(textwrap.dedent(source), encoding="utf-8")
        yield path


@contextmanager
def candidate(**kwargs: Any) -> Iterator[Candidate]:
    with candidate_dir(**kwargs) as path:
        yield load_candidate_unchecked(path)
