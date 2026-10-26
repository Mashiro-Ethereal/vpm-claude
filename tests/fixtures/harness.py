"""Harness configuration and a small input package for CPU tests."""

import json
from pathlib import Path
from typing import Any

import yaml

from .reference import ROOT


def harness_config(runs: Path) -> dict[str, Any]:
    config = yaml.safe_load((ROOT / "configs/default.yaml").read_text(encoding="utf-8"))
    config["paths"]["runs"] = str(runs)
    return config


def small_package(root: Path) -> Path:
    package = root / "packages/PickCube-v1"
    (package / "example/candidate").mkdir(parents=True)
    for name in ("TASK.md", "candidate_api.md", "example/candidate/notes.md"):
        (package / name).write_text(name, encoding="utf-8")
    (package / "manifest.json").write_text(json.dumps({
        "env_id": "PickCube-v1", "package_sha256": "package-hash-from-manifest"}), encoding="utf-8")
    return package
