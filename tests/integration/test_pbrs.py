"""PBRS with ManiSkill auto-reset in one isolated GPU worker."""

import os
import unittest

from scripts.pbrs_smoke import defaults, run_worker


@unittest.skipUnless(os.environ.get("VPM_INTEGRATION") == "1", "set VPM_INTEGRATION=1")
class PBRSIntegrationTest(unittest.TestCase):
    def test_random_rollouts_across_auto_resets(self) -> None:
        config = defaults()
        result = run_worker("smoke", config["gamma"], config["r_bonus"])
        self.assertEqual((result["num_envs"], result["steps"]), (16, 120))
        self.assertGreaterEqual(result["min_resets"], 2)
        self.assertLessEqual(result["max_telescope_error"], 1e-5)
