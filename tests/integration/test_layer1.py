"""Real GPU first-layer checks, one environment per worker subprocess."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest

from tests.fixtures.mutations import Edit
from tests.fixtures.reference import GRASP_RETURN, NEAR_RETURN, REFERENCE, reference_copy
from vpmkit.candidate import check_static
from vpmkit.validate.check_sh import write_check_sh
from vpmkit.validate.layer1 import run_layer1


@unittest.skipUnless(os.environ.get("VPM_INTEGRATION") == "1", "set VPM_INTEGRATION=1")
class Layer1IntegrationTest(unittest.TestCase):
    def test_reference(self) -> None:
        report = run_layer1(REFERENCE, "PickCube-v1")
        self.assertTrue(report.layer1_passed, report.to_markdown())
        self.assertEqual(report.groups, dict.fromkeys(("parse", "schema", "ast", "run"), "passed"))
        self.assertEqual(report.problems, [])
        print(f"\nReference layer1 wall time: {report.timing['total_seconds']:.3f} s", flush=True)

    def test_mutations(self) -> None:
        cases = [
            ("shape", Edit("predicates.py", NEAR_RETURN, "return g.pos[:, :1]"),
             "run.output", "near(g, cube)", "shape=(8, 1)"),
            ("cpu_output", Edit("predicates.py", NEAR_RETURN, "return torch.zeros(w.batch_size)"),
             "run.output", "near(g, cube)", "device=cpu"),
            ("cpu_arithmetic", Edit("predicates.py", NEAR_RETURN,
                                    "return g.pos[:, 0] + torch.zeros(w.batch_size)"),
             "run.error", "predicates.py:", "RuntimeError"),
            ("progress_division", Edit("progress.py", "/ d0", "/ (d0 - d0)"),
             "run.nonfinite", "progress_reach", "NaN or Inf"),
            ("official_key", Edit("stage_graph.yaml", "key: is_grasped", "key: is_grasp"),
             "run.official_key", "stage_graph.yaml: official[0].key", "is_grasp"),
            ("binding", Edit("bindings.py", "api.actor(env.cube,", "api.actor(env.cubee,"),
             "run.bind", "bindings.py:", "AttributeError"),
        ]
        for name, edit, code, location, message in cases:
            with self.subTest(name=name), reference_copy(edit) as path:
                self.assertTrue(check_static(path).passed)
                report = run_layer1(path, "PickCube-v1")
                self.assertFalse(report.layer1_passed)
                self.assertEqual(report.groups["run"], "failed")
                self.assertEqual(len(report.problems), 1, report.to_markdown())
                problem = report.problems[0]
                self.assertEqual(problem.code, code, report.to_markdown())
                if location.endswith(":"):
                    self.assertRegex(problem.location, rf"{location}\d+$")
                    lineno = int(problem.location.split(":")[-1])
                    self.assertIn(edit.new, (path / edit.file).read_text().splitlines()[lineno - 1])
                else:
                    self.assertEqual(problem.location, location)
                self.assertIn(message, problem.message)
                self.assertIn("seed=0, step=0", problem.message)

    def test_two_failing_predicates(self) -> None:
        with reference_copy(Edit("predicates.py", NEAR_RETURN, "return g.pos[:, :1]"),
                            Edit("predicates.py", GRASP_RETURN, "return o.pos[:, :1]")) as path:
            report = run_layer1(path, "PickCube-v1")
        self.assertEqual([(p.code, p.location) for p in report.problems],
                         [("run.output", "near(g, cube)"), ("run.output", "grasped(g, cube)")])

    def test_each_missing_official_key(self) -> None:
        with reference_copy(Edit("stage_graph.yaml", "key: is_grasped", "key: is_grasp"),
                            Edit("stage_graph.yaml", "key: is_obj_placed", "key: is_place")) as path:
            report = run_layer1(path, "PickCube-v1")
        self.assertEqual([(p.code, p.location) for p in report.problems],
                         [("run.official_key", "stage_graph.yaml: official[0].key"),
                          ("run.official_key", "stage_graph.yaml: official[1].key")])

    def test_check_sh_minimal_environment(self) -> None:
        keys = {"HOME", "PATH", "LANG", "LANGUAGE", "LC_ALL", "CUDA_VISIBLE_DEVICES"}
        environment = {key: value for key, value in os.environ.items()
                       if key in keys or key.lower().endswith("_proxy")}
        environment["CUDA_VISIBLE_DEVICES"] = "1"
        with tempfile.TemporaryDirectory(prefix="check workspace ") as folder:
            workspace = Path(folder)
            candidate = workspace / "candidate"
            shutil.copytree(REFERENCE, candidate)
            write_check_sh(workspace, "PickCube-v1")
            started = time.perf_counter()
            result = subprocess.run(["./check.sh"], cwd=workspace, env=environment,
                                    capture_output=True, text=True, timeout=900)
            elapsed = time.perf_counter() - started
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Check report: PASSED", result.stdout)
            print(f"\ncheck.sh cold process wall time: {elapsed:.3f} s", flush=True)
            Edit("predicates.py", NEAR_RETURN, "return g.pos[:, :1]").apply(candidate)
            result = subprocess.run([str(workspace / "check.sh")], cwd=workspace.parent, env=environment,
                                    capture_output=True, text=True, timeout=900)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("run.output", result.stdout)
            self.assertIn("Check report: FAILED", result.stdout)
