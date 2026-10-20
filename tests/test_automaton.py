import unittest

import torch

from vpmkit.runtime.automaton import CompiledInvariant, automaton_step, compile_tables


class AutomatonTests(unittest.TestCase):
    def step(self, tables, stage, value, counters=None, debounce=2):
        stage = torch.as_tensor(stage, dtype=torch.long)
        value = torch.as_tensor(value, dtype=torch.bool)
        if counters is None:
            counters = torch.zeros((len(stage), tables.J), dtype=torch.int32)
        return automaton_step(stage, counters, value, tables, debounce)

    def test_single_multi_advance_and_negated_guard(self):
        tables = compile_tables([[(0, True)], [(1, True)], [(2, False)]], [], 3)
        stage, counters, event, regressed = self.step(
            tables, [0, 0, 0, 0],
            [[True, False, True], [True, True, True], [True, True, False], [False, True, False]],
        )
        self.assertEqual(stage.tolist(), [1, 2, 3, 0])
        self.assertEqual(counters.shape, (4, 0))
        self.assertEqual(event.tolist(), [-1] * 4)
        self.assertFalse(regressed.any())

    def test_debounce_and_recovery_reset(self):
        tables = compile_tables([[(0, True)], [(1, True)], [(2, True)]],
                                [CompiledInvariant(2, 0, True, 1, "lost")], 3)
        first = self.step(tables, [2], [[False, True, False]])
        self.assertEqual(first[0].tolist(), [2])
        self.assertEqual(first[1].tolist(), [[1]])
        self.assertEqual(first[2].tolist(), [-1])
        recovered = self.step(tables, first[0], [[True, True, False]], first[1])
        self.assertEqual(recovered[1].tolist(), [[0]])
        second = self.step(tables, first[0], [[False, True, False]], first[1])
        self.assertEqual(second[0].tolist(), [1])
        self.assertEqual(second[1].tolist(), [[0]])
        self.assertEqual(second[2].tolist(), [0])
        self.assertTrue(second[3].all())
        # Stage 1's exit is already true, but regression forbids advance this call.
        third = self.step(tables, second[0], [[False, True, False]], second[1])
        self.assertEqual(third[0].tolist(), [2])

    def test_minimum_target_and_lowest_id_tie(self):
        inv = [CompiledInvariant(3, 0, True, 2, "later"),
               CompiledInvariant(3, 1, True, 0, "first minimum"),
               CompiledInvariant(3, 2, False, 0, "second minimum")]
        tables = compile_tables([[(0, True)]] * 4, inv, 3)
        result = self.step(tables, [3, 3], [[False, False, True], [False, True, False]], debounce=1)
        self.assertEqual(result[0].tolist(), [0, 2])
        self.assertEqual(result[2].tolist(), [1, 0])
        self.assertTrue(result[3].all())

    def test_new_stage_invariants_wait_and_counters_reset(self):
        tables = compile_tables([[(0, True)], [(1, True)]],
                                [CompiledInvariant(1, 2, True, 0, "restore")], 3)
        first = self.step(tables, [0], [[True, False, False]], torch.tensor([[1]], dtype=torch.int32))
        self.assertEqual(first[0].tolist(), [1])
        self.assertEqual(first[1].tolist(), [[0]])
        second = self.step(tables, first[0], [[True, False, False]], first[1])
        self.assertEqual(second[1].tolist(), [[1]])
        advanced = self.step(tables, [1], [[True, True, False]], torch.zeros(1, 1, dtype=torch.int32))
        self.assertEqual(advanced[0].tolist(), [2])
        self.assertEqual(advanced[1].tolist(), [[0]])

    def test_done_entered_and_left_with_debounce(self):
        tables = compile_tables([[(0, True)], [(1, False)]],
                                [CompiledInvariant(2, 1, False, 1, "release")], 2)
        done = self.step(tables, [0], [[True, False]])
        self.assertEqual(done[0].tolist(), [2])
        transient = self.step(tables, done[0], [[True, True]], done[1])
        self.assertEqual(transient[0].tolist(), [2])
        regressed = self.step(tables, transient[0], [[True, True]], transient[1])
        self.assertEqual(regressed[0].tolist(), [1])
        self.assertTrue(regressed[3].all())

    def test_inputs_are_not_mutated(self):
        tables = compile_tables([[(0, True)]], [CompiledInvariant(1, 0, True, 0, "restore")], 1)
        stage, counters, value = torch.tensor([1]), torch.tensor([[1]], dtype=torch.int32), torch.tensor([[False]])
        automaton_step(stage, counters, value, tables, 2)
        self.assertEqual(stage.tolist(), [1])
        self.assertEqual(counters.tolist(), [[1]])
        self.assertEqual(value.tolist(), [[False]])
