"""Environment loading helpers."""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(env_path: Path, *, override: bool = False) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip()
        if override or normalized_key not in os.environ:
            os.environ[normalized_key] = normalized_value
