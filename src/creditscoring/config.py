"""Load pipeline settings from a YAML file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "default.yaml"


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Read the settings in ``path`` (``configs/default.yaml`` by default)."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
