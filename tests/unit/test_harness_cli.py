"""CLI card selection, sequential runs and repository-relative defaults."""

from contextlib import redirect_stdout
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import yaml

from tests.fixtures.harness import harness_config
from tests.fixtures.reference import ROOT
from vpmkit.harness.backends import ClaudeCodeBackend, ScriptedBackend
from vpmkit.harness.run import Verdict
from vpmkit.validate import VPM_PYTHON


class HarnessCliTest(unittest.TestCase):
    def test_gpu_override_k_runs_and_backend_configuration(self) -> None:
        spec = importlib.util.spec_from_file_location("generation_cli", ROOT / "scripts/run_generation.py")
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            config = harness_config(root / "runs")
            config["k"] = 2
            config["gpu"] = 0
            config["review"] = {"max_turns": 7, "timeout_s": 12}
            path = root / "config.yaml"
            path.write_text(yaml.safe_dump(config))
            directories = {"XDG_CACHE_HOME": root / "outputs/cache",
                           "MS_ASSET_DIR": root / "outputs/maniskill", "TMPDIR": root / "outputs/tmp"}
            for name in ("scripted", "claude"):
                backends = []

                def run(env_id: str, backend, effective: dict) -> Verdict:
                    self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], "1")
                    self.assertEqual(effective["gpu"], 1)
                    self.assertEqual(env_id, "PickCube-v1")
                    for variable, directory in directories.items():
                        self.assertEqual(os.environ[variable], str(directory))
                        self.assertTrue(directory.is_dir())
                    self.assertIsInstance(backend, ScriptedBackend if name == "scripted" else ClaudeCodeBackend)
                    if name == "claude":
                        self.assertEqual((backend.max_turns, backend.timeout_s), (80, 2400))
                        self.assertEqual((backend.review_max_turns, backend.review_timeout_s), (7, 12))
                    backends.append(backend)
                    return Verdict("passed", root / f"run-{len(backends)}", [{}])

                argv = ["run_generation.py", "--env", "PickCube-v1", "--gpu", "1",
                        "--backend", name, "--config", str(path)]
                output = io.StringIO()
                inherited = {"CLAUDE_CODE_ENTRYPOINT": "nested-test",
                             **dict.fromkeys(directories, "caller-value")}
                with patch("sys.argv", argv), patch.dict(os.environ, inherited), patch.object(cli, "REPO_ROOT", root), \
                        patch("vpmkit.harness.run.run_generation", side_effect=run), redirect_stdout(output):
                    self.assertEqual(cli.main(), 0)
                self.assertEqual(len(backends), 2)
                self.assertIsNot(backends[0], backends[1])
                self.assertIn("run-1: passed", output.getvalue())
                self.assertIn("run-2: passed", output.getvalue())

    def test_help_from_outside_repository(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([str(VPM_PYTHON), str(ROOT / "scripts/run_generation.py"), "--help"],
                                    cwd=folder, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--backend {claude,scripted}", result.stdout)
