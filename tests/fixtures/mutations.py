"""Exact edits of the legal example, with expected check codes and locations."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edit:
    file: str
    old: str | None
    new: str | None

    def apply(self, directory: Path) -> None:
        path = directory / self.file
        if self.new is None:
            path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.old is None:
            text = self.new
        else:
            text = path.read_text(encoding="utf-8")
            if self.old == "":
                text += self.new
            elif self.old not in text:
                raise AssertionError(f"Mutation text not found in {self.file}: {self.old!r}")
            else:
                text = text.replace(self.old, self.new, 1)
        path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class Mutation:
    name: str
    code: str
    location: str
    edits: tuple[Edit, ...]
    also_codes: tuple[str, ...] = ()

    @property
    def codes(self) -> set[str]:
        return {self.code, *self.also_codes}

    def apply(self, directory: Path) -> None:
        for edit in self.edits:
            edit.apply(directory)


YAML = "stage_graph.yaml"
NEAR_PARAM = "  - {name: near.max_dist, default: 0.02, range: [0.0, 0.05]}\n"
PROGRESS_PARAM = "  - {name: progress.reach.d0, default: 0.3, range: [0.1, 0.6]}\n"
OBJECTS = "objects:\n  g:    {name: the gripper}\n  cube: {name: the red cube}\n  pad:  {name: the target pad}\n"
NEAR_TRUE = 'need_true="{g} is far from {o}; move {g} to {o}."'


MUTATIONS = [
    Mutation("yaml_unclosed_list", "parse.yaml", "stage_graph.yaml:2:1",
             (Edit(YAML, None, "task: [\n"),)),
    Mutation("python_nested_syntax", "parse.python", "helpers/broken.py:1",
             (Edit("helpers/broken.py", None, "def broken(:\n"),)),
    Mutation("format_extra_key", "schema.format", "stage_graph.yaml: surprise",
             (Edit(YAML, "", "surprise: 1\n"),)),
    Mutation("format_top_level", "schema.format", "stage_graph.yaml",
             (Edit(YAML, None, "[1, 2]\n"),)),
    Mutation("format_empty_objects", "schema.format", "stage_graph.yaml: objects",
             (Edit(YAML, OBJECTS, "objects: {}\n"),)),
    Mutation("format_empty_stages", "schema.format", "stage_graph.yaml: stages",
             (Edit(YAML, None, "task: Test\n" + OBJECTS + "stages: []\nofficial: []\n"),)),
    Mutation("format_wrong_type", "schema.format", "stage_graph.yaml: stages[0].exit",
             (Edit(YAML, 'exit: ["near(g, cube)"]', 'exit: "near(g, cube)"'),)),
    Mutation("format_missing_field", "schema.format", "stage_graph.yaml: stages[0].exit",
             (Edit(YAML, '    exit: ["near(g, cube)"]\n', ""),)),
    Mutation("format_duplicate_stage", "schema.format", "stage_graph.yaml",
             (Edit(YAML, "official:\n", '  - {name: reach, exit: ["near(g, cube)"]}\nofficial:\n'),)),
    Mutation("format_duplicate_param", "schema.format", "stage_graph.yaml",
             (Edit(YAML, "", NEAR_PARAM),)),
    Mutation("literal_invalid", "schema.literal_syntax", "stage_graph.yaml: official[0].literals[0]",
             (Edit(YAML, '["grasped(g, cube)"], key: is_cube_grasped', '["grasped()"], key: is_cube_grasped'),)),
    Mutation("predicate_unknown", "schema.unknown_predicate", "stage_graph.yaml: official[0].literals[0]",
             (Edit(YAML, '["grasped(g, cube)"], key: is_cube_grasped', '["missing(g, cube)"], key: is_cube_grasped'),)),
    Mutation("literal_arity", "schema.arity", "stage_graph.yaml: official[0].literals[0]",
             (Edit(YAML, '["grasped(g, cube)"], key: is_cube_grasped', '["grasped(g)"], key: is_cube_grasped'),)),
    Mutation("object_unknown", "schema.unknown_object", "stage_graph.yaml: official[0].literals[0]",
             (Edit(YAML, '["grasped(g, cube)"], key: is_cube_grasped', '["grasped(g, missing)"], key: is_cube_grasped'),)),
    Mutation("binding_missing", "schema.binding_keys", "bindings.py:7",
             (Edit("bindings.py", '        "pad": api.actor(env.pad, half_size=env.pad_half_size),\n', ""),)),
    Mutation("binding_extra", "schema.binding_keys", "bindings.py:7",
             (Edit("bindings.py", '        "g": api.gripper(),', '        "g": api.gripper(),\n        "extra": api.gripper(),'),)),
    Mutation("binding_duplicate", "schema.binding_keys", "bindings.py:7",
             (Edit("bindings.py", '        "g": api.gripper(),', '        "g": api.gripper(),\n        "g": api.gripper(),'),)),
    Mutation("binding_not_dict", "schema.binding_keys", "bindings.py:2",
             (Edit("bindings.py", None, 'def bind(env, api):\n    return dict(g=1, cube=2, pad=3)\n'),)),
    Mutation("binding_nonstring", "schema.binding_keys", "bindings.py:7",
             (Edit("bindings.py", '"pad": api.actor', '42: api.actor'),)),
    Mutation("binding_unpack", "schema.binding_keys", "bindings.py:7",
             (Edit("bindings.py", '        "g": api.gripper(),', '        **{},\n        "g": api.gripper(),'),)),
    Mutation("binding_not_last", "schema.binding_keys", "bindings.py:12",
             (Edit("bindings.py", "", "    value = 1\n"),)),
    Mutation("binding_signature", "schema.binding_keys", "bindings.py:4",
             (Edit("bindings.py", "def bind(env, api):", "def bind(environment, api):"),)),
    Mutation("binding_missing_function", "schema.binding_keys", "bindings.py:1",
             (Edit("bindings.py", "def bind(env, api):", "def other(env, api):"),)),
    Mutation("binding_duplicate_function", "schema.binding_keys", "bindings.py:13",
             (Edit("bindings.py", "", '\ndef bind(env, api):\n    return {"g": 1, "cube": 2, "pad": 3}\n'),)),
    Mutation("predicate_first_parameter", "schema.predicate_signature", "predicates.py:21",
             (Edit("predicates.py", "def near(w, g, o,", "def near(world, g, o,"),)),
    Mutation("predicate_duplicate", "schema.predicate_signature", "predicates.py:21",
             (Edit("predicates.py", "", "\ndef near(w, g, o, max_dist=0.02):\n    return 1\n"),)),
    Mutation("predicate_nested", "schema.predicate_signature", "predicates.py:5",
             (Edit("predicates.py", "import torch\n", 'import torch\ndef outer():\n'
                   '    @predicate(desc="Unused", need_true="move", scale=1)\n'
                   '    def unused(w, o):\n        return 1\n'),)),
    Mutation("progress_unknown_stage", "schema.progress_signature", "progress.py:9",
             (Edit("progress.py", "progress_reach", "progress_missing"),
              Edit(YAML, "progress.reach.d0", "progress.missing.d0"))),
    Mutation("progress_first_parameters", "schema.progress_signature", "progress.py:9",
             (Edit("progress.py", "(w, o, d0=0.3)", "(world, o, d0=0.3)"),)),
    Mutation("progress_default_expression", "schema.progress_signature", "progress.py:9",
             (Edit("progress.py", "d0=0.3", "d0=0.1 + 0.2"),)),
    Mutation("progress_varargs", "schema.progress_signature", "progress.py:9",
             (Edit("progress.py", "(w, o, d0=0.3)", "(w, o, *args, d0=0.3)"),)),
    Mutation("progress_kwargs", "schema.progress_signature", "progress.py:9",
             (Edit("progress.py", "(w, o, d0=0.3)", "(w, o, d0=0.3, **kwargs)"),)),
    Mutation("guard_empty", "schema.empty_guard", "stage_graph.yaml: stages[0].exit",
             (Edit(YAML, "stages:\n", "stages:\n  - {name: first, exit: []}\n"),)),
    Mutation("regress_unknown", "schema.regress_target", "stage_graph.yaml: stages[1].invariants[0].regress_to",
             (Edit(YAML, 'literal: "near(g, cube)", regress_to: reach', 'literal: "near(g, cube)", regress_to: missing'),)),
    Mutation("regress_self", "schema.regress_target", "stage_graph.yaml: stages[1].invariants[0].regress_to",
             (Edit(YAML, 'literal: "near(g, cube)", regress_to: reach', 'literal: "near(g, cube)", regress_to: grasp'),)),
    Mutation("regress_first_stage", "schema.regress_target", "stage_graph.yaml: stages[0].invariants[0].regress_to",
             (Edit(YAML, 'exit: ["near(g, cube)"]', 'exit: ["near(g, cube)"]\n'
                   '    invariants: [{literal: "near(g, cube)", regress_to: reach}]'),)),
    Mutation("guard_contradiction", "schema.guard_contradiction", "stage_graph.yaml: stages[0].exit[1]",
             (Edit(YAML, 'exit: ["near(g, cube)"]', 'exit: ["near(g, cube)", "not near ( g,cube )"]'),)),
    Mutation("invariant_conflict_positive", "schema.invariant_conflict", "stage_graph.yaml: stages[1].invariants[0].literal",
             (Edit(YAML, 'exit: ["grasped(g, cube)"]', 'exit: ["grasped(g, cube)", "not near(g,cube)"]'),)),
    Mutation("invariant_conflict_negative", "schema.invariant_conflict", "stage_graph.yaml: stages[1].invariants[0].literal",
             (Edit(YAML, 'exit: ["near(g, cube)"]', 'exit: ["not near(g, cube)"]'),
              Edit(YAML, 'literal: "near(g, cube)"', 'literal: "not near(g, cube)"'),
              Edit(YAML, 'exit: ["grasped(g, cube)"]', 'exit: ["grasped(g, cube)", "near(g,cube)"]'))),
    Mutation("regress_after_establishing_guard", "schema.regress_too_late", "stage_graph.yaml: stages[2].invariants[0].regress_to",
             (Edit(YAML, 'literal: "grasped(g, cube)", regress_to: reach', 'literal: "near(g, cube)", regress_to: grasp'),)),
    Mutation("success_missing", "schema.success", "stage_graph.yaml: official",
             (Edit(YAML, "key: success", "key: finished"),)),
    Mutation("success_mismatch", "schema.success", "stage_graph.yaml: official[3].literals",
             (Edit(YAML, '["on(cube, pad)", "static(cube)", "not grasped(g, cube)"]',
                   '["on(cube, pad)", "not grasped(g, cube)"]'),)),
    Mutation("official_empty", "schema.official_format", "stage_graph.yaml: official[0].literals",
             (Edit(YAML, '["grasped(g, cube)"], key: is_cube_grasped', '[], key: is_cube_grasped'),)),
    Mutation("official_duplicate_key", "schema.official_format", "stage_graph.yaml: official[2].key",
             (Edit(YAML, "key: is_cube_static", "key: is_cube_on_pad"),)),
    Mutation("official_tunable_threshold", "schema.official_threshold", "stage_graph.yaml: params[2].name",
             (Edit(YAML, "", "  - {name: on.z_tol, default: 0.005, range: [0, 1]}\n"),)),
    Mutation("official_unknown_threshold", "schema.official_threshold", "stage_graph.yaml: params[2].name",
             (Edit(YAML, "", "  - {name: on.missing, default: 0.005, range: [0, 1]}\n"),)),
    Mutation("param_missing_predicate", "schema.param_missing", "stage_graph.yaml: params",
             (Edit(YAML, NEAR_PARAM, ""),)),
    Mutation("param_missing_progress", "schema.param_missing", "stage_graph.yaml: params",
             (Edit(YAML, PROGRESS_PARAM, ""),)),
    Mutation("param_equal_bounds", "schema.param_value", "stage_graph.yaml: params[0].range",
             (Edit(YAML, "range: [0.0, 0.05]", "range: [0.02, 0.02]"),)),
    Mutation("param_reversed_bounds", "schema.param_value", "stage_graph.yaml: params[0].range",
             (Edit(YAML, "range: [0.0, 0.05]", "range: [0.05, 0.0]"),)),
    Mutation("param_outside_range", "schema.param_value", "stage_graph.yaml: params[0].default",
             (Edit(YAML, "range: [0.0, 0.05]", "range: [0.03, 0.05]"),)),
    Mutation("param_signature_mismatch", "schema.param_value", "stage_graph.yaml: params[0].default",
             (Edit(YAML, "default: 0.02", "default: 0.03"),)),
    Mutation("param_progress_mismatch", "schema.param_value", "stage_graph.yaml: params[1].default",
             (Edit(YAML, "default: 0.3", "default: 0.30000000000000004"),)),
    Mutation("template_missing_desc", "schema.template", "predicates.py:12",
             (Edit("predicates.py", "    desc=(", "    description=("),)),
    Mutation("template_nonliteral", "schema.template", "predicates.py:12",
             (Edit("predicates.py", NEAR_TRUE, "need_true=GUIDANCE"),)),
    Mutation("template_blank", "schema.template", "predicates.py:12",
             (Edit("predicates.py", NEAR_TRUE, 'need_true=" "'),)),
    Mutation("template_negated_missing_false", "schema.template", "predicates.py:26",
             (Edit("predicates.py", '    need_false="{o} is still held; release {o}.",\n', ""),)),
    Mutation("template_extra_keyword", "schema.template", "predicates.py:12",
             (Edit("predicates.py", "    scale=0.3,", "    scale=0.3, surprise=1,"),)),
    Mutation("import_disallowed", "ast.import", "predicates.py:3",
             (Edit("predicates.py", "import torch\n", "import torch\nimport random\n"),)),
    Mutation("import_nested", "ast.import", "predicates.py:9",
             (Edit("predicates.py", "    return torch.linalg.norm", "    import random\n    return torch.linalg.norm"),)),
    Mutation("import_progress_relative", "ast.import", "progress.py:6",
             (Edit("progress.py", "from .predicates", "from ..predicates"),)),
    Mutation("import_predicate_relative", "ast.import", "predicates.py:3",
             (Edit("predicates.py", "import torch\n", "import torch\nfrom .predicates import helper\n"),)),
    Mutation("name_read", "ast.name_access", "predicates.py:9",
             (Edit("predicates.py", "g.pos - o.pos", "g.name - o.pos"),)),
]

for file in (YAML, "bindings.py", "predicates.py", "notes.md"):
    MUTATIONS.append(Mutation("missing_" + file.replace(".", "_"), "parse.missing_file", file,
                              (Edit(file, None, None),)))

for name, signature in {
    "no_objects": "w",
    "positional_only": "w, /, o",
    "varargs": "w, o, *args",
    "kwargs": "w, o, **kwargs",
    "required_keyword": "w, o, *, threshold",
    "keyword_object": "w, *, o",
    "bool_default": "w, o, threshold=True",
    "name_default": "w, o, threshold=LIMIT",
    "expression_default": "w, o, threshold=1 / 2",
    "unary_plus": "w, o, threshold=+1",
}.items():
    source = ('import torch\n\n@predicate(desc="Unused", need_true="move", scale=1)\n'
              f'def unused({signature}):\n    return 1\n')
    MUTATIONS.append(Mutation("signature_" + name, "schema.predicate_signature", "predicates.py:5",
                              (Edit("predicates.py", "import torch\n", source),)))

for name in ("runtime.debounce", "near.missing", "unused.threshold", "progress.reach.missing", "progress.ghost.d0"):
    MUTATIONS.append(Mutation("param_unknown_" + name, "schema.param_unknown", "stage_graph.yaml: params[2].name",
                              (Edit(YAML, "", f"  - {{name: {name}, default: 1, range: [0, 2]}}\n"),)))

for name, value in {"zero": "0", "negative": "-1", "bool": "True", "expression": "0.1 + 0.2"}.items():
    MUTATIONS.append(Mutation("template_scale_" + name, "schema.template", "predicates.py:12",
                              (Edit("predicates.py", "scale=0.3", "scale=" + value),)))

for name, value in {
    "unknown": "{unknown}", "threshold": "{max_dist}", "conversion": "{o!r}",
    "format": "{o:.2f}", "empty": "{}", "stray": "move {", "doubled": "{{o}}",
}.items():
    MUTATIONS.append(Mutation("placeholder_" + name, "schema.template_placeholder", "predicates.py:17",
                              (Edit("predicates.py", NEAR_TRUE, f'need_true="{value}"'),)))

for method in ("item", "tolist", "numpy", "cpu"):
    MUTATIONS.append(Mutation("host_" + method, "ast.host_transfer", "predicates.py:9",
                              (Edit("predicates.py", "g.pos - o.pos", f"g.pos.{method}() - o.pos"),)))

for name, source in {
    "for": "for value in []:\n    pass",
    "async_for": "async def helper():\n    async for value in stream:\n        pass",
    "while": "while False:\n    pass",
    "list": "values = [value for value in ()]",
    "set": "values = {value for value in ()}",
    "dict": "values = {value: value for value in ()}",
    "generator": "values = (value for value in ())",
}.items():
    line = 4 if name == "async_for" else 3
    MUTATIONS.append(Mutation("loop_" + name, "ast.loop", f"predicates.py:{line}",
                              (Edit("predicates.py", "import torch\n", "import torch\n" + source + "\n"),)))

for name, source in {
    "open": "open('data')",
    "exec": "exec('value = 1')",
    "eval": "eval('1')",
    "compile": "compile('1', 'code', 'eval')",
    "import_call": "__import__('math')",
    "os": "import os",
    "nested_import": "def helper():\n    from pathlib import Path",
    "dunder_attribute": "value = object.__class__",
    "dunder_name": "__value__ = 1",
    "dunder_alias": "import math as __math__",
    "dunder_import": "from math import __doc__",
    "dunder_function": "def __helper__(): pass",
    "dunder_class": "class __Helper__: pass",
    "dunder_argument": "def helper(__value__): pass",
    "dunder_keyword": "helper(__value__=1)",
}.items():
    line = 2 if name == "nested_import" else 1
    MUTATIONS.append(Mutation("unsafe_" + name, "ast.unsafe", f"helpers/unsafe.py:{line}",
                              (Edit("helpers/unsafe.py", None, source + "\n"),)))
