"""Pure tensor updates for a linear stage automaton."""

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class CompiledInvariant:
    owner: int
    instance: int
    positive: bool
    target: int
    event: str


@dataclass(frozen=True)
class AutomatonTables:
    K: int
    I: int
    exits: tuple[tuple[tuple[int, bool], ...], ...]
    invariants: tuple[CompiledInvariant, ...]
    exit_positive: Tensor
    exit_negative: Tensor
    inv_owner: Tensor
    inv_instance: Tensor
    inv_positive: Tensor
    inv_target: Tensor

    @property
    def J(self):
        return len(self.invariants)


def compile_tables(exits, invariants, num_instances, device="cpu") -> AutomatonTables:
    """Compile lists of (instance, polarity) exits and global invariants."""
    exits = tuple(tuple(row) for row in exits)
    invariants = tuple(invariants)
    positive = torch.zeros((len(exits), num_instances), dtype=torch.bool, device=device)
    negative = torch.zeros_like(positive)
    for k, literals in enumerate(exits):
        for instance, polarity in literals:
            (positive if polarity else negative)[k, instance] = True
    return AutomatonTables(
        len(exits), num_instances, exits, invariants, positive, negative,
        torch.tensor([inv.owner for inv in invariants], dtype=torch.long, device=device),
        torch.tensor([inv.instance for inv in invariants], dtype=torch.long, device=device),
        torch.tensor([inv.positive for inv in invariants], dtype=torch.bool, device=device),
        torch.tensor([inv.target for inv in invariants], dtype=torch.long, device=device),
    )


def automaton_step(stage, counters, value, tables, debounce):
    """Update a batch without modifying any input tensor or looping over rows."""
    new_stage = stage.clone()
    event = torch.full_like(stage, -1)
    regressed = torch.zeros_like(stage, dtype=torch.bool)
    if tables.J:
        active = stage[:, None] == tables.inv_owner[None, :]
        truth = torch.where(tables.inv_positive, value[:, tables.inv_instance], ~value[:, tables.inv_instance])
        new_counters = torch.where(active & ~truth, counters + 1, 0)
        triggered = active & (new_counters >= debounce)
        regressed = triggered.any(dim=1)
        target = torch.where(triggered, tables.inv_target, tables.K + 1).amin(dim=1)
        eligible = triggered & (tables.inv_target[None, :] == target[:, None])
        ids = torch.arange(tables.J, device=stage.device)
        selected = torch.where(eligible, ids, tables.J).amin(dim=1)
        event = torch.where(regressed, selected, event)
        new_stage = torch.where(regressed, target, new_stage)
    else:
        new_counters = torch.zeros_like(counters)

    exits_hold = (
        (~tables.exit_positive[None, :, :] | value[:, None, :])
        & (~tables.exit_negative[None, :, :] | ~value[:, None, :])
    ).all(dim=2)
    for _ in range(tables.K):
        current_holds = exits_hold.gather(1, new_stage.clamp(max=tables.K - 1)[:, None]).squeeze(1)
        advance = ~regressed & (new_stage < tables.K) & current_holds
        new_stage = new_stage + advance.long()
    reset = regressed | (new_stage != stage)
    new_counters = torch.where(reset[:, None], 0, new_counters)
    return new_stage, new_counters, event, regressed
