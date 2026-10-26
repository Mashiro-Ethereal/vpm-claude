"""Construct the environment shared by generating and reviewing agents."""

import os
from collections.abc import Mapping


ALLOWED_NAMES = (
    "HOME", "PATH", "LANG", "LANGUAGE", "LC_ALL",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
)


def child_env(gpu: int | str) -> dict[str, str]:
    environment = {name: os.environ[name] for name in ALLOWED_NAMES if name in os.environ}
    environment["CUDA_VISIBLE_DEVICES"] = str(gpu)
    return environment


def env_names(env: Mapping[str, str]) -> list[str]:
    return sorted(env)
