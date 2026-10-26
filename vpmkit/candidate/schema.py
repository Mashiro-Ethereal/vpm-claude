"""The structural schema of stage_graph.yaml."""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
import yaml


Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z_][a-z0-9_]*$")]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ObjectDecl(_Model):
    name: str


class Invariant(_Model):
    literal: str
    regress_to: str


class Stage(_Model):
    name: Identifier
    exit: list[str]
    invariants: list[Invariant] = Field(default_factory=list)


class Official(_Model):
    literals: list[str]
    key: str


class Param(_Model):
    name: str
    default: float
    range: tuple[float, float]


class StageGraph(_Model):
    task: str
    objects: dict[Identifier, ObjectDecl] = Field(min_length=1)
    stages: list[Stage] = Field(min_length=1)
    official: list[Official]
    params: list[Param] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_names(self) -> "StageGraph":
        for label, entries in (("stage", self.stages), ("param", self.params)):
            names = [entry.name for entry in entries]
            if len(set(names)) != len(names):
                raise ValueError(f"{label} names must be unique")
        return self

    @classmethod
    def from_yaml(cls, path: str | Path) -> "StageGraph":
        with Path(path).open(encoding="utf-8") as stream:
            return cls.model_validate(yaml.safe_load(stream))

    def stage_index(self, name: str) -> int:
        for index, stage in enumerate(self.stages):
            if stage.name == name:
                return index
        raise ValueError(f"unknown stage {name!r}")

    def param_defaults(self) -> dict[str, float]:
        return {param.name: param.default for param in self.params}
