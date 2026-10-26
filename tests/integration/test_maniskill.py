"""ManiSkill checks isolated to one environment in each worker process."""

import json
import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
PYTHON = "/home/zxh/anaconda3/envs/vpm-mani/bin/python"


@unittest.skipUnless(os.environ.get("VPM_INTEGRATION") == "1", "set VPM_INTEGRATION=1")
class ManiSkillIntegrationTest(unittest.TestCase):
    def worker(self, mode: str) -> dict:
        (ROOT / "outputs/tmp").mkdir(parents=True, exist_ok=True)
        environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "1",
                       "TMPDIR": str(ROOT / "outputs/tmp"),
                       "XDG_CACHE_HOME": str(ROOT / "outputs/cache"),
                       "MS_ASSET_DIR": str(ROOT / "outputs/maniskill"),
                       "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(
            ["bash", "-c", 'ulimit -c 0; exec "$@"', "worker", PYTHON,
             "-m", "tests.integration.maniskill_worker", mode],
            cwd=ROOT, env=environment, text=True, capture_output=True, timeout=240)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_gpu_snapshots(self) -> None:
        result = self.worker("gpu")
        self.assertEqual((result["device"], result["num_envs"], result["states"]), ("cuda", 8, 11))
        self.assertTrue(result["unchanged_after_step"])
        self.assertTrue(result["hidden_actor_checked"])
        self.assertTrue(all(abs(z) < 1e-6 for z in result["table"]["world_top_z"]))
        print("\nGPU table evidence: " + json.dumps(result["table"]), flush=True)

    def test_cpu_snapshots(self) -> None:
        result = self.worker("cpu")
        self.assertEqual((result["device"], result["num_envs"], result["states"]), ("cpu", 1, 11))
        self.assertTrue(result["unchanged_after_step"])
        self.assertTrue(result["hidden_actor_checked"])

    def test_scripted_grasp(self) -> None:
        result = self.worker("grasp")
        self.assertIsNotNone(result["first_grasp_step"], result)
        self.assertGreater(result["grasped_steps"], 0)
        print("\nScripted grasp: " + json.dumps(result), flush=True)

    def test_scene_inventory(self) -> None:
        result = self.worker("inventory")
        text = result["markdown"]
        self.assertIn("| `env.cube` | `cube` | dynamic | [0.02, 0.02, 0.02] in all environments |", text)
        self.assertIn("| `env.goal_site` | `goal_site` | visual only |", text)
        self.assertIn("3 seeds × 8 parallel environments = 24.", text)
        self.assertIn("| `self.goal_thresh` | 0.025 | yes |", text)
        for key in ("success", "is_obj_placed", "is_robot_static", "is_grasped"):
            self.assertIn(f"| `{key}` | bool [N] |", text)
        self.assertNotIn("reward", text.lower())
        self.assertEqual(Path(result["path"]).read_text(encoding="utf-8"), text)
