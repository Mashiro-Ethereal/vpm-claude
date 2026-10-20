import json
from pathlib import Path
import tempfile
import unittest

import torch

from tests import TOY, world
from tests.test_validate_layer1_unit import successful_trajectory
from vpmkit.artifact.loader import load_candidate
from vpmkit.runtime.teacher import Teacher
from vpmkit.validate.replay import Trajectory, load_trajectories, replay_summary, save_trajectories
from vpmkit.world import WorldState


class ReplaySummaryTests(unittest.TestCase):
    def setUp(self):
        self.teacher = Teacher(load_candidate(TOY), 1)

    def test_transitions_and_aggregate(self):
        summary = replay_summary(self.teacher, [successful_trajectory()])
        json.dumps(summary, allow_nan=False)
        item = summary["trajectories"][0]
        self.assertEqual(item["transitions"], [
            {"frame": 1, "from": "reach", "to": "grasp"},
            {"frame": 2, "from": "grasp", "to": "carry"},
            {"frame": 4, "from": "carry", "to": "release"},
            {"frame": 5, "from": "release", "to": "done"},
        ])
        self.assertEqual(item["final_stage"], "done")
        self.assertIsNone(item["stuck"])
        self.assertEqual(item["literal_flicker"]["grasped(g, block)"], 2)
        self.assertEqual(item["literal_flicker"]["not grasped(g, block)"], 2)
        self.assertEqual(item["stage_segments"][2]["spearman"], 1.0)
        self.assertIsNone(item["stage_segments"][0]["spearman"])
        self.assertEqual(len(item["phi_jumps"]), 4)
        self.assertAlmostEqual(item["phi_jumps"][-1]["delta"], 0.125)
        self.assertEqual(summary["aggregate"]["fraction_reaching_stage"]["done"], 1.)
        self.assertEqual(summary["aggregate"]["median_frames_per_stage"]["carry"], 2)

    def test_stuck_thresholds_flicker_and_regressions(self):
        frames = [world(block_x=0.05), world(block_x=0.2, held=True),
                  world(block_x=0.4), world(block_x=0.5),
                  world(block_x=0.6, held=True), world(block_x=0.8, held=True)]
        summary = replay_summary(self.teacher, [Trajectory(WorldState.cat(frames), False, "stuck")])
        item = summary["trajectories"][0]
        self.assertEqual(item["regressions"], [{"frame": 3, "event": "Regrasp block with gripper."}])
        self.assertFalse(item["done"])
        self.assertEqual(item["stuck"]["stage"], "carry")
        self.assertEqual(item["stuck"]["max_progress_frame"], 5)
        literal = item["stuck"]["unmet_exit_literals"][0]
        self.assertEqual(literal["literal"], "in_region(block, region)")
        self.assertEqual(literal["thresholds"], {"radius": 0.05})
        self.assertAlmostEqual(literal["margin"], -0.15, places=6)
        self.assertEqual(item["literal_flicker"]["grasped(g, block)"], 3)
        self.assertEqual(summary["aggregate"]["most_frequent_stuck_literal"], literal["literal"])

    def test_constant_and_tied_progress_correlations(self):
        constant = Trajectory(WorldState.cat([world(), world()]), False, "constant")
        tied = Trajectory(WorldState.cat([world(block_x=0.3), world(block_x=0.3), world(block_x=0.2)]), False, "tied")
        summary = replay_summary(self.teacher, [constant, tied])
        self.assertIsNone(summary["trajectories"][0]["stage_segments"][0]["spearman"])
        self.assertAlmostEqual(summary["trajectories"][1]["stage_segments"][0]["spearman"], 0.8660254038)

    def test_immediate_transitions_count_crossed_stages(self):
        frames = WorldState.cat([world(g_x=1., block_x=1., held=True), world(block_x=1.)])
        summary = replay_summary(self.teacher, [Trajectory(frames, True, "jump")])
        self.assertEqual(summary["trajectories"][0]["transitions"][0], {"frame": 0, "from": "reach", "to": "release"})
        self.assertEqual(summary["aggregate"]["fraction_reaching_stage"]["carry"], 1.0)
        self.assertEqual(summary["aggregate"]["median_frames_per_stage"]["carry"], 0)

    def test_plain_tensor_serialization(self):
        original = successful_trajectory()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "trajs.pt"
            save_trajectories(path, [original])
            plain = torch.load(path, weights_only=True)
            self.assertIsInstance(plain[0]["states"]["objects"]["g"], dict)
            restored = load_trajectories(path)[0]
        self.assertEqual(restored.source, original.source)
        self.assertTrue(restored.success)
        restored.states.validate()
        self.assertEqual(restored.states.meta, original.states.meta)
        self.assertEqual(restored.states.device, torch.device("cpu"))
        for name, obj in original.states.objects.items():
            actual = restored.states.objects[name]
            for field in ("pos", "quat", "linvel", "angvel", "half_size"):
                torch.testing.assert_close(getattr(actual, field), getattr(obj, field))
            for key in obj.attrs:
                torch.testing.assert_close(actual.attrs[key], obj.attrs[key])
        for field in ("grasping", "contacts", "official"):
            for key, tensor in getattr(original.states, field).items():
                torch.testing.assert_close(getattr(restored.states, field)[key], tensor)
        self.assertEqual(replay_summary(self.teacher, [restored]), replay_summary(self.teacher, [original]))


if __name__ == "__main__":
    unittest.main()
