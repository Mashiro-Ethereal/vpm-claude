"""Package rendering and publication without creating a simulation environment."""

import hashlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from mani_skill.agents.robots.panda.panda import Panda
from mani_skill.utils.registration import REGISTERED_ENVS

from vpmkit.adapters.maniskill.helpers_table import HELPERS, TASK_HELPERS
from vpmkit.package import build
from vpmkit.package.helpers import render_helpers_py


EXAMPLE_FILES = {
    "env_source.py", "helpers.py", "scene_inventory.md", "candidate/stage_graph.yaml",
    "candidate/bindings.py", "candidate/predicates.py", "candidate/progress.py", "candidate/notes.md",
}
PACKAGE_ENTRIES = {"TASK.md", "env_source.py", "helpers.py", "scene_inventory.md",
                   "candidate_api.md", "example", "manifest.json"}


class RenderHelpersTest(unittest.TestCase):
    def test_pick_cube(self) -> None:
        rendered = render_helpers_py("PickCube-v1")
        example = (build.RESOURCES / "example/helpers.py").read_text(encoding="utf-8")
        self.assertEqual(rendered.splitlines()[0], example.splitlines()[0])
        separator = next(line for line in example.splitlines() if line.startswith("# ---"))
        self.assertEqual(rendered.count(separator), 2)
        previous = -1
        for helper_id, call in TASK_HELPERS["PickCube-v1"]:
            position = rendered.index(f"# {call}\n")
            self.assertGreater(position, previous)
            previous = position
            self.assertIn(f"#   {HELPERS[helper_id].defined_at}\n", rendered)
        self.assertIn("w.grasping(g, o)", rendered)
        self.assertIn("g.arm_qvel", rendered)
        self.assertEqual(rendered.count("#   Source not included."), 1)
        self.assertNotIn("def is_grasping", rendered)
        self.assertIn(textwrap.dedent(inspect.getsource(Panda.is_static)), rendered)
        self.assertNotIn("example task", rendered)

    def test_no_entries(self) -> None:
        header = (build.RESOURCES / "example/helpers.py").read_text().splitlines()[0]
        self.assertEqual(render_helpers_py("StackPyramid-v1"),
                         header + "\n# evaluate() calls no helper outside the task class.\n")


class BuildPackageTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

        def inventory(env_id: str, destination: Path) -> None:
            self.assertEqual(env_id, "PickCube-v1")
            destination.write_text("# Mock scene inventory\n", encoding="utf-8")

        patcher = patch.object(build, "_write_scene_inventory", side_effect=inventory)
        self.inventory = patcher.start()
        self.addCleanup(patcher.stop)

    def test_contents_template_and_manifest(self) -> None:
        resources = self.root / "resources"
        shutil.copytree(build.RESOURCES / "example", resources / "example")
        (resources / "example/unrelated.txt").write_text("excluded")
        cache = resources / "example/__pycache__"
        cache.mkdir(exist_ok=True)
        (cache / "unrelated.pyc").write_bytes(b"excluded")
        with patch.object(build, "RESOURCES", resources):
            package = build.build_package("PickCube-v1", self.root / "packages")
        self.inventory.assert_called_once()
        self.assertEqual({item.name for item in package.iterdir()}, PACKAGE_ENTRIES)
        self.assertEqual({path.relative_to(package / "example").as_posix()
                          for path in (package / "example").rglob("*") if path.is_file()}, EXAMPLE_FILES)
        for relative in EXAMPLE_FILES:
            self.assertEqual((package / "example" / relative).read_bytes(),
                             (build.RESOURCES / "example" / relative).read_bytes())
        self.assertEqual((package / "candidate_api.md").read_bytes(), build.CANDIDATE_API.read_bytes())
        task = (package / "TASK.md").read_text(encoding="utf-8")
        for name in ("env_id", "class_name", "robot_uid", "max_episode_steps", "docstring"):
            self.assertNotIn("{" + name + "}", task)
        self.assertIn("PickCube-v1", task)
        self.assertIn("PickCubeEnv", task)
        self.assertIn("robot `panda`, at most 50 steps", task)
        self.assertIn(inspect.getdoc(REGISTERED_ENVS["PickCube-v1"].cls), task)
        source = (package / "env_source.py").read_text()
        self.assertEqual(len(source.splitlines()), 186)
        self.assertNotIn("reward", source)
        manifest = json.loads((package / "manifest.json").read_text())
        self.assertEqual(manifest["env_id"], "PickCube-v1")
        self.assertEqual(manifest["maniskill_version"], "3.0.1")
        self.assertEqual(manifest["source_file"], "envs/tasks/tabletop/pick_cube.py")
        paths = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
        self.assertEqual(set(manifest["files"]), paths - {"manifest.json"})
        records = []
        for relative, entry in sorted(manifest["files"].items()):
            digest = hashlib.sha256((package / relative).read_bytes()).hexdigest()
            self.assertEqual(entry["sha256"], digest)
            self.assertTrue(entry["source"])
            self.assertFalse(entry["source"].startswith("/"))
            records.append(relative.encode() + b"\0" + digest.encode() + b"\n")
        self.assertEqual(manifest["package_sha256"], hashlib.sha256(b"".join(records)).hexdigest())

    def test_template_preserves_other_braces_and_rejects_unresolved_placeholder(self) -> None:
        template = self.root / "TASK_template.md"
        template.write_text("{env_id} {class_name} {robot_uid} {max_episode_steps} {docstring} {other}")
        facts = dict(zip(build.PLACEHOLDERS, ("PickCube-v1", "PickCubeEnv", "panda", "50", "doc")))
        with patch.object(build, "TASK_TEMPLATE", template):
            self.assertEqual(build._render_task(facts), "PickCube-v1 PickCubeEnv panda 50 doc {other}")
            facts["docstring"] = "Unresolved {env_id}"
            with self.assertRaisesRegex(ValueError, "Unresolved TASK.md placeholders:.*env_id"):
                build._render_task(facts)

    def test_planned_interface_refused(self) -> None:
        candidate_api = self.root / "candidate_api.md"
        candidate_api.write_bytes(build.CANDIDATE_API.read_bytes() + b"\n<!-- Planned interface -->\n")
        with patch.object(build, "CANDIDATE_API", candidate_api):
            with self.assertRaisesRegex(ValueError, "<!-- Planned interface"):
                build.build_package("PickCube-v1", self.root / "packages")
        self.inventory.assert_not_called()
        self.assertFalse((self.root / "packages").exists())

    def test_existing_package_and_overwrite(self) -> None:
        package = build.build_package("PickCube-v1", self.root)
        extra = package / "obsolete.txt"
        extra.write_text("old")
        self.inventory.reset_mock()
        with self.assertRaises(FileExistsError):
            build.build_package("PickCube-v1", self.root)
        self.inventory.assert_not_called()
        self.assertTrue(extra.exists())
        self.assertEqual(build.build_package("PickCube-v1", self.root, overwrite=True), package)
        self.assertFalse(extra.exists())
        self.assertEqual(list(self.root.iterdir()), [package])

    def test_failed_inventory_cleans_staging_and_preserves_destination(self) -> None:
        package = self.root / "PickCube-v1"
        with self.subTest(existing=False):
            self.inventory.side_effect = RuntimeError("inventory failed")
            with self.assertRaisesRegex(RuntimeError, "inventory failed"):
                build.build_package("PickCube-v1", self.root)
            self.assertEqual(list(self.root.iterdir()), [])
        with self.subTest(existing=True):
            package.mkdir()
            (package / "keep.txt").write_text("old contents")
            with self.assertRaisesRegex(RuntimeError, "inventory failed"):
                build.build_package("PickCube-v1", self.root, overwrite=True)
            self.assertEqual(list(self.root.iterdir()), [package])
            self.assertEqual((package / "keep.txt").read_text(), "old contents")


class InventorySubprocessTest(unittest.TestCase):
    def test_inherits_gpu_and_disables_core_dumps(self) -> None:
        with patch.dict(build.os.environ, {"CUDA_VISIBLE_DEVICES": "1"}):
            with patch.object(build.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
                build._write_scene_inventory("PickCube-v1", build.REPO_ROOT / "outputs/tmp/inventory.md")
        args, kwargs = run.call_args
        self.assertIn(str(build.VPM_PYTHON), args[0])
        self.assertEqual(args[0][:3], ["bash", "-c", 'ulimit -c 0; exec "$@"'])
        self.assertEqual(kwargs["env"]["CUDA_VISIBLE_DEVICES"], "1")
        self.assertEqual(kwargs["env"]["XDG_CACHE_HOME"], str(build.REPO_ROOT / "outputs/cache"))
