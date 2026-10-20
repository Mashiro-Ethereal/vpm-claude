"""Predicate evaluation, automaton state, progress, and rendered guidance."""

from dataclasses import dataclass
from types import SimpleNamespace

import torch
from torch import Tensor

from ..artifact.literals import parse_literal
from ..world import ObjView, WorldState, WorldView, bool_margin
from .automaton import CompiledInvariant, automaton_step, compile_tables


class TeacherError(ValueError):
    pass


@dataclass
class TeacherOutput:
    stage: Tensor
    stage_progress: Tensor
    progress_raw: Tensor
    phi: Tensor
    margin: Tensor
    value: Tensor
    need_true: Tensor
    need_false: Tensor
    event: Tensor
    regressed: Tensor
    done: Tensor


class Teacher:
    def __init__(self, candidate, num_envs, device="cpu"):
        if type(num_envs) is not int or num_envs < 1:
            raise ValueError("num_envs must be a positive integer")
        self.candidate = candidate
        self.num_envs = num_envs
        self.stage = torch.zeros(num_envs, dtype=torch.long, device=device)
        self.device = self.stage.device
        graph = candidate.graph
        self.K = len(graph.stages)
        instances, indices = [], {}

        def register(text):
            literal = parse_literal(text)
            if literal.instance_key not in indices:
                indices[literal.instance_key] = len(instances)
                instances.append(literal)

        for stage in graph.stages:
            for text in stage.exit:
                register(text)
        for stage in graph.stages:
            for inv in stage.invariants:
                register(inv.literal)
        for decl in graph.official:
            for text in decl.literals:
                register(text)
        self.instances = tuple(instances)
        self.instance_keys = tuple(literal.instance_key for literal in instances)
        self.I = len(instances)

        def ref(text):
            literal = parse_literal(text)
            return indices[literal.instance_key], literal.positive

        exits = [tuple(ref(text) for text in stage.exit) for stage in graph.stages]
        stage_indices = {stage.name: k for k, stage in enumerate(graph.stages)}
        invariants = []
        for k, stage in enumerate(graph.stages):
            for inv in stage.invariants:
                instance, positive = ref(inv.literal)
                invariants.append(CompiledInvariant(
                    k, instance, positive, stage_indices[inv.regress_to],
                    inv.event.format(**candidate.display_names),
                ))
        for instance, positive in exits[-1]:
            invariants.append(CompiledInvariant(
                self.K, instance, positive, self.K - 1,
                self._literal_guidance(instance, positive),
            ))
        for inv in graph.stages[-1].invariants:
            instance, positive = ref(inv.literal)
            invariants.append(CompiledInvariant(
                self.K, instance, positive, stage_indices[inv.regress_to],
                inv.event.format(**candidate.display_names),
            ))
        self.tables = compile_tables(exits, invariants, self.I, self.device)
        self.counters = torch.zeros((num_envs, self.tables.J), dtype=torch.int32, device=self.device)

    def _literal_guidance(self, instance, positive):
        literal = self.instances[instance]
        spec = self.candidate.predicate_specs[literal.pred]
        template = spec.need_true if positive else spec.need_false
        names = {param: self.candidate.display_names[handle]
                 for param, handle in zip(spec.obj_params, literal.args)}
        try:
            return template.format(**names)
        except (AttributeError, KeyError, IndexError, ValueError) as exc:
            raise TeacherError(f"{literal.instance_key}: invalid guidance template: {exc}") from exc

    def _world(self, ws):
        if ws.device.type != self.device.type or (
            ws.device.index is not None and ws.device.index != self.device.index
        ):
            raise TeacherError(f"WorldState is on {ws.device}; teacher is on {self.device}")
        try:
            objects = {handle: ObjView(ws.objects[handle], handle) for handle in self.candidate.graph.objects}
        except KeyError as exc:
            raise TeacherError(f"WorldState is missing object {exc.args[0]!r}") from exc
        return WorldView(ws), objects

    def _result(self, result, n, label, boolean_margin=False):
        if not isinstance(result, Tensor) or tuple(result.shape) != (n,):
            shape = tuple(result.shape) if isinstance(result, Tensor) else type(result).__name__
            raise TeacherError(f"{label}: expected tensor shape [{n}], got {shape}")
        if result.device != self.device:
            raise TeacherError(f"{label}: result must be on {self.device}, got {result.device}")
        if result.is_complex():
            raise TeacherError(f"{label}: result must be real")
        if result.dtype == torch.bool and boolean_margin:
            result = bool_margin(result)
        else:
            result = result.to(dtype=torch.float32)
        if not torch.isfinite(result).all():
            raise TeacherError(f"{label}: result contains NaN or Inf")
        return result

    def evaluate(self, ws: WorldState):
        """Evaluate each distinct predicate instance once, independently of state."""
        w, objects = self._world(ws)
        margins = []
        for literal in self.instances:
            spec = self.candidate.predicate_specs[literal.pred]
            thresholds = {name: self.candidate.params.get(f"{literal.pred}.{name}", default)
                          for name, default in spec.thresholds.items()}
            try:
                result = self.candidate.predicates[literal.pred](
                    w, *(objects[h] for h in literal.args), **thresholds,
                )
            except Exception as exc:
                raise TeacherError(f"{literal.instance_key}: {type(exc).__name__}: {exc}") from exc
            margins.append(self._result(result, ws.N, literal.instance_key, boolean_margin=True))
        margin = torch.stack(margins, dim=1)
        return margin, margin >= 0

    def progress_all(self, ws, margin, value):
        w, objects = self._world(ws)
        namespace = SimpleNamespace(**objects)
        raw = []
        for k, stage in enumerate(self.candidate.graph.stages):
            if stage.name in self.candidate.progress:
                spec = self.candidate.progress_specs[stage.name]
                params = {name: self.candidate.params.get(f"progress.{stage.name}.{name}", default)
                          for name, default in spec.params.items()}
                try:
                    result = self.candidate.progress[stage.name](w, namespace, **params)
                except Exception as exc:
                    raise TeacherError(f"progress_{stage.name}: {type(exc).__name__}: {exc}") from exc
                result = self._result(result, ws.N, f"progress_{stage.name}")
            else:
                terms = []
                for instance, positive in self.tables.exits[k]:
                    s = margin[:, instance] if positive else -margin[:, instance]
                    truth = value[:, instance] if positive else ~value[:, instance]
                    scale = self.candidate.predicate_specs[self.instances[instance].pred].scale
                    terms.append(torch.where(truth, 1.0, (1.0 + s / scale).clamp(0.0, 1.0)))
                result = torch.stack(terms, dim=1).mean(dim=1)
            raw.append(result)
        return torch.stack(raw, dim=1)

    def reset(self, mask=None, stage=None):
        if mask is None:
            mask = torch.ones(self.num_envs, dtype=torch.bool, device=self.device)
        if not isinstance(mask, Tensor) or mask.dtype != torch.bool or mask.shape != (self.num_envs,):
            raise ValueError(f"reset mask must be a BoolTensor[{self.num_envs}]")
        mask = mask.to(self.device)
        stage = 0 if stage is None else stage
        target = torch.as_tensor(stage, device=self.device)
        if target.dtype != torch.long or target.shape not in ((), (self.num_envs,)):
            raise ValueError("reset stage must be an integer or a LongTensor[num_envs]")
        if ((target < 0) | (target > self.K)).any():
            raise ValueError(f"reset stage must be between 0 and {self.K}")
        self.stage = torch.where(mask, target, self.stage)
        self.counters = torch.where(mask[:, None], 0, self.counters)

    def _output(self, stage, raw, margin, value, event, regressed):
        done = stage == self.K
        current = stage.clamp(max=self.K - 1)
        progress = raw.clamp(0.0, 1.0).gather(1, current[:, None]).squeeze(1)
        progress = torch.where(done, 0.0, progress)
        phi = torch.where(done, 1.0, (stage.to(torch.float32) + progress) / self.K)
        need_true = self.tables.exit_positive[current] & ~value & ~done[:, None]
        need_false = self.tables.exit_negative[current] & value & ~done[:, None]
        return TeacherOutput(stage.clone(), progress, raw, phi, margin, value,
                             need_true, need_false, event, regressed, done)

    def step(self, ws: WorldState) -> TeacherOutput:
        if ws.N != self.num_envs:
            raise TeacherError(f"step expects N={self.num_envs}, got {ws.N}")
        margin, value = self.evaluate(ws)
        stage, counters, event, regressed = automaton_step(
            self.stage, self.counters, value, self.tables, self.candidate.graph.runtime.debounce,
        )
        raw = self.progress_all(ws, margin, value)
        output = self._output(stage, raw, margin, value, event, regressed)
        self.stage, self.counters = stage, counters
        return output

    def run_sequence(self, ws_frames, initial_stage=0) -> TeacherOutput:
        """Replay one trajectory; leave the teacher's live batch state unchanged."""
        if type(initial_stage) is not int or not 0 <= initial_stage <= self.K:
            raise ValueError(f"initial_stage must be an integer between 0 and {self.K}")
        margin, value = self.evaluate(ws_frames)
        raw = self.progress_all(ws_frames, margin, value)
        stage = torch.full((1,), initial_stage, dtype=torch.long, device=self.device)
        counters = torch.zeros((1, self.tables.J), dtype=torch.int32, device=self.device)
        stages, events, regressions = [], [], []
        for t in range(ws_frames.N):
            stage, counters, event, regressed = automaton_step(
                stage, counters, value[t:t+1], self.tables, self.candidate.graph.runtime.debounce,
            )
            stages.append(stage)
            events.append(event)
            regressions.append(regressed)
        if not stages:
            empty = torch.empty(0, dtype=torch.long, device=self.device)
            return self._output(empty, raw, margin, value, empty.clone(), empty.bool())
        return self._output(torch.cat(stages), raw, margin, value, torch.cat(events), torch.cat(regressions))

    def render_guidance(self, out, row) -> list[str]:
        stage = int(out.stage[row])
        if stage == self.K:
            return []
        return [self._literal_guidance(instance, positive)
                for instance, positive in self.tables.exits[stage]
                if (out.need_true if positive else out.need_false)[row, instance]]

    def render_event(self, event_id) -> str:
        event_id = int(event_id)
        if event_id == -1:
            return ""
        if not 0 <= event_id < self.tables.J:
            raise ValueError(f"Invalid invariant event id {event_id}")
        return self.tables.invariants[event_id].event
