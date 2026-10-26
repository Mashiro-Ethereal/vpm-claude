"""Create a writable candidate workspace beside harness-owned records."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

from ..validate.check_sh import write_check_sh
from .env import child_env


@dataclass(frozen=True)
class Run:
    path: Path
    env_id: str
    gpu: int | str

    @property
    def workspace(self) -> Path:
        return self.path / "workspace"

    @property
    def records(self) -> Path:
        return self.path / "records"


def create_run(package_dir: str | Path, runs_root: str | Path,
               env_id: str, gpu: int | str) -> Run:
    parent = Path(runs_root).resolve() / env_id
    parent.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = 0
    while True:
        path = parent / (run_id if suffix == 0 else f"{run_id}-{suffix}")
        try:
            path.mkdir()
        except FileExistsError:
            suffix += 1
        else:
            break
    run = Run(path, env_id, gpu)
    shutil.copytree(package_dir, run.workspace)
    for entry in run.workspace.rglob("*"):
        entry.chmod(0o555 if entry.is_dir() else 0o444)
    run.workspace.chmod(0o755)
    (run.workspace / "candidate").mkdir()
    write_check_sh(run.workspace, env_id).chmod(0o555)
    run.records.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=run.workspace, env=child_env(gpu),
                   stdin=subprocess.DEVNULL, capture_output=True, check=True)
    return run
