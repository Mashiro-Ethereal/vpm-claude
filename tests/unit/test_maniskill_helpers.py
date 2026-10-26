"""Helper metadata follows the installed ManiSkill source."""

import inspect
import unittest
from unittest.mock import patch

from mani_skill.envs.tasks.tabletop.pick_cube import PickCubeEnv

from vpmkit.adapters.maniskill.helpers_table import HELPERS, TASK_HELPERS


class HelpersTest(unittest.TestCase):
    def test_source_and_call_text(self) -> None:
        self.assertIn("get_qvel()[..., :-2]", HELPERS["Panda.is_static"].source())
        self.assertIn("linear_velocity", HELPERS["Actor.is_static"].source())
        self.assertTrue(HELPERS["Panda.is_static"].source_included)
        self.assertTrue(HELPERS["Actor.is_static"].source_included)
        source = inspect.getsource(PickCubeEnv.evaluate)
        for helper_id, call in TASK_HELPERS["PickCube-v1"]:
            self.assertIn(helper_id, HELPERS)
            self.assertIn(call, source)
        for helper_id, helper in HELPERS.items():
            self.assertEqual(helper.id, helper_id)
            self.assertIn("def ", helper.source())
            if helper_id not in ("Panda.is_static", "Actor.is_static"):
                self.assertFalse(helper.source_included)

    def test_source_is_extracted_at_call_time(self) -> None:
        with patch("vpmkit.adapters.maniskill.helpers_table.inspect.getsource", return_value="source now") as getsource:
            self.assertEqual(HELPERS["Panda.is_static"].source(), "source now")
            getsource.assert_called_once()
