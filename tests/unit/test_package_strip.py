"""Reward removal against installed task sources and exact line preservation."""

import inspect
from pathlib import Path
import unittest

import mani_skill.envs
from mani_skill.utils.registration import REGISTERED_ENVS

from vpmkit.package.strip import ResidualRewardError, strip_reward_functions


PASSING = {
    "PickCube-v1": (216, 186),
    "LiftPegUpright-v1": (144, 111),
    "StackCube-v1": (186, 145),
    "PegInsertionSide-v1": (360, 300),
    "StackPyramid-v1": (196, 196),
    "PushCube-v1": (250, 212),
    "PullCube-v1": (151, 128),
    "RollBall-v1": (181, 153),
    "PlaceSphere-v1": (258, 216),
    "PickSingleYCB-v1": (259, 230),
    "PokeCube-v1": (230, 193),
    "PlugCharger-v1": (282, 282),
    "AssemblingKits-v1": (293, 293),
}
BLOCKED = {
    "PullCubeTool-v1": [215],
    "TurnFaucet-v1": [204, 205, 206, 212, 216, 219, 220, 224, 226, 227, 228, 231, 233, 236, 237],
    "PushT-v1": [406, 420, 426, 431],
}


def task_source(env_id: str) -> str:
    return Path(inspect.getsourcefile(REGISTERED_ENVS[env_id].cls)).read_bytes().decode("utf-8")


class StripTest(unittest.TestCase):
    def test_passing_task_sources(self) -> None:
        for env_id, counts in PASSING.items():
            with self.subTest(env_id=env_id):
                source = task_source(env_id)
                result = strip_reward_functions(source)
                self.assertEqual((len(source.splitlines()), len(result.text.splitlines())), counts)
                self.assertNotIn("reward", result.text)
                lines = source.splitlines(keepends=True)
                for name, first, last in reversed(result.removed):
                    self.assertIn(name, ("compute_dense_reward", "compute_normalized_dense_reward"))
                    del lines[first - 1:last]
                self.assertEqual(result.text, "".join(lines))
                if counts[0] == counts[1]:
                    self.assertEqual(result.removed, [])

    def test_blocked_task_sources(self) -> None:
        for env_id, line_numbers in BLOCKED.items():
            with self.subTest(env_id=env_id):
                source = task_source(env_id)
                with self.assertRaises(ResidualRewardError) as caught:
                    strip_reward_functions(source)
                expected = [f"{number}: {source.splitlines()[number - 1]}" for number in line_numbers]
                self.assertEqual(str(caught.exception).splitlines()[1:], expected)

    def test_decorators_multiple_classes_and_line_endings(self) -> None:
        source = (
            "# retained\r\n"
            "class First:\r\n"
            "    SUPPORTED_REWARD_MODES = ()\r\n"
            "    @decorate(\r\n"
            "        'argument',\r\n"
            "    )\r\n"
            "    @another\r\n"
            "    def compute_dense_reward(self):\r\n"
            "        # removed with the function\r\n"
            "        return 1\r\n"
            "    # retained after the function\r\n"
            "\n"
            "class Second:\n"
            "    async def compute_normalized_dense_reward(self):\n"
            "        return 2\n"
            "\n"
            "    def evaluate(self):\n"
            "        return True"
        )
        result = strip_reward_functions(source)
        self.assertEqual(result.removed, [("compute_dense_reward", 4, 10),
                                          ("compute_normalized_dense_reward", 14, 15)])
        lines = source.splitlines(keepends=True)
        self.assertEqual(result.text, "".join(lines[:3] + lines[10:13] + lines[15:]))

    def test_residual_numbers_refer_to_stripped_text(self) -> None:
        source = "def compute_dense_reward():\n    return 1\n\n# reward remains\nvalue = 'rewards'\n"
        with self.assertRaises(ResidualRewardError) as caught:
            strip_reward_functions(source)
        self.assertEqual(str(caught.exception).splitlines()[1:],
                         ["2: # reward remains", "3: value = 'rewards'"])
