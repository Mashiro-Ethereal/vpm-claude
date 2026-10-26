"""Build reproducible input packages with inventory sampling in a subprocess."""

import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .helpers import render_helpers_py
from .strip import strip_reward_functions


REPO_ROOT = Path(__file__).resolve().parents[2]
VPM_PYTHON = Path("/home/zxh/anaconda3/envs/vpm-mani/bin/python")
RESOURCES = REPO_ROOT / "vpmkit/resources"
TASK_TEMPLATE = RESOURCES / "TASK_template.md"
CANDIDATE_API = RESOURCES / "candidate_api.md"
EXAMPLE_FILES = (
    "env_source.py", "helpers.py", "scene_inventory.md",
    "candidate/stage_graph.yaml", "candidate/bindings.py", "candidate/predicates.py",
    "candidate/progress.py", "candidate/notes.md",
)
PLACEHOLDERS = ("env_id", "class_name", "robot_uid", "max_episode_steps", "docstring")


def _render_task(facts: dict[str, str]) -> str:
    text = TASK_TEMPLATE.read_text(encoding="utf-8")
    for name in PLACEHOLDERS:
        text = text.replace("{" + name + "}", facts[name])
    remaining = ["{" + name + "}" for name in PLACEHOLDERS if "{" + name + "}" in text]
    if remaining:
        raise ValueError("Unresolved TASK.md placeholders: " + ", ".join(remaining))
    return text


def _write_scene_inventory(env_id: str, destination: Path) -> None:
    tmp = REPO_ROOT / "outputs/tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "TMPDIR": str(tmp),
                   "XDG_CACHE_HOME": str(REPO_ROOT / "outputs/cache"),
                   "MS_ASSET_DIR": str(REPO_ROOT / "outputs/maniskill"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from vpmkit.adapters.maniskill.inventory import scene_inventory\n"
        "Path(sys.argv[2]).write_text(scene_inventory(sys.argv[1]), encoding='utf-8')\n"
    )
    result = subprocess.run(
        ["bash", "-c", 'ulimit -c 0; exec "$@"', "inventory", str(VPM_PYTHON),
         "-c", code, env_id, str(destination.resolve())],
        cwd=REPO_ROOT, env=environment, capture_output=True, text=True, timeout=240)
    if result.returncode:
        raise RuntimeError(f"Scene inventory failed for {env_id} (exit {result.returncode}):\n"
                           + result.stdout + result.stderr)


def build_package(env_id: str, out_root: str | Path = "outputs/stage1/packages",
                  overwrite: bool = False) -> Path:
    destination = Path(out_root) / env_id
    if destination.exists() and not overwrite:
        raise FileExistsError(destination)
    candidate_api = CANDIDATE_API.read_bytes()
    if b"<!-- Planned interface" in candidate_api:
        raise ValueError(f"{CANDIDATE_API} still contains '<!-- Planned interface'")

    import mani_skill
    import mani_skill.envs  # Registers the environments.
    from mani_skill.utils.registration import REGISTERED_ENVS

    registration = REGISTERED_ENVS[env_id]
    cls = registration.cls
    source_path = Path(inspect.getsourcefile(cls))
    source_file = source_path.resolve().relative_to(Path(mani_skill.__file__).resolve().parent).as_posix()
    source = strip_reward_functions(source_path.read_bytes().decode("utf-8")).text
    task = _render_task({
        "env_id": env_id,
        "class_name": cls.__name__,
        "robot_uid": str(inspect.signature(cls.__init__).parameters["robot_uids"].default),
        "max_episode_steps": str(registration.max_episode_steps),
        "docstring": inspect.getdoc(cls) or "",
    })
    helpers = render_helpers_py(env_id)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{env_id}-", dir=destination.parent) as folder:
        staging = Path(folder)
        (staging / "env_source.py").write_bytes(source.encode("utf-8"))
        (staging / "TASK.md").write_text(task, encoding="utf-8")
        (staging / "helpers.py").write_text(helpers, encoding="utf-8")
        (staging / "candidate_api.md").write_bytes(candidate_api)
        _write_scene_inventory(env_id, staging / "scene_inventory.md")
        sources = {
            "env_source.py": f"mani_skill/{source_file} (reward functions removed)",
            "TASK.md": "vpmkit/resources/TASK_template.md",
            "helpers.py": f"vpmkit/adapters/maniskill/helpers_table.py: TASK_HELPERS[{env_id!r}], HELPERS",
            "candidate_api.md": "vpmkit/resources/candidate_api.md",
            "scene_inventory.md": "vpmkit/adapters/maniskill/inventory.py: "
                                  f"scene_inventory({env_id!r}, seeds=(0, 1, 2), num_envs=8)",
        }
        for relative in EXAMPLE_FILES:
            target = staging / "example" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RESOURCES / "example" / relative, target)
            sources[f"example/{relative}"] = f"vpmkit/resources/example/{relative}"
        files = {relative: {"sha256": hashlib.sha256((staging / relative).read_bytes()).hexdigest(),
                            "source": sources[relative]}
                 for relative in sorted(sources)}
        package_hash_input = "".join(f"{relative}\0{entry['sha256']}\n"
                                     for relative, entry in files.items())
        manifest = {
            "env_id": env_id,
            "maniskill_version": mani_skill.__version__,
            "source_file": source_file,
            "files": files,
            "package_sha256": hashlib.sha256(package_hash_input.encode("utf-8")).hexdigest(),
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if destination.exists():
            shutil.rmtree(destination)
        staging.rename(destination)
    return destination
