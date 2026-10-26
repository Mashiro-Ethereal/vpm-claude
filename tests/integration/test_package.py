"""Reproducible packages built from isolated GPU inventory samples."""

import json
import os
from pathlib import Path
import tempfile
import unittest

from vpmkit.package.build import build_package


@unittest.skipUnless(os.environ.get("VPM_INTEGRATION") == "1", "set VPM_INTEGRATION=1")
class PackageIntegrationTest(unittest.TestCase):
    def test_pick_cube_reproducibility(self) -> None:
        with tempfile.TemporaryDirectory() as first_root, tempfile.TemporaryDirectory() as second_root:
            first = build_package("PickCube-v1", first_root)
            second = build_package("PickCube-v1", second_root)

            def files(package: Path) -> dict[str, bytes]:
                return {path.relative_to(package).as_posix(): path.read_bytes()
                        for path in package.rglob("*") if path.is_file()}

            first_files = files(first)
            self.assertEqual(first_files, files(second))
            self.assertEqual({path.name for path in first.iterdir()},
                             {"TASK.md", "env_source.py", "helpers.py", "scene_inventory.md",
                              "candidate_api.md", "example", "manifest.json"})
            self.assertEqual({path for path in first_files if path.startswith("example/")}, {
                "example/env_source.py", "example/helpers.py", "example/scene_inventory.md",
                "example/candidate/stage_graph.yaml", "example/candidate/bindings.py",
                "example/candidate/predicates.py", "example/candidate/progress.py", "example/candidate/notes.md",
            })
            source = first_files["env_source.py"].decode("utf-8")
            self.assertEqual(len(source.splitlines()), 186)
            self.assertNotIn("reward", source)
            inventory = first_files["scene_inventory.md"].decode("utf-8")
            self.assertIn("| `self.goal_thresh` | 0.025 | yes |", inventory)
            task = first_files["TASK.md"].decode("utf-8")
            self.assertIn("PickCube-v1", task)
            self.assertIn("PickCubeEnv", task)
            self.assertIn("robot `panda`, at most 50 steps", task)
            first_manifest = json.loads(first_files["manifest.json"])
            second_manifest = json.loads((second / "manifest.json").read_text())
            self.assertEqual(first_manifest["package_sha256"], second_manifest["package_sha256"])
            print("\nReproducible PickCube-v1 package_sha256: " + first_manifest["package_sha256"], flush=True)
