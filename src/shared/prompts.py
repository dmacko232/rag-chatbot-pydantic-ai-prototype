from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


@lru_cache
def _load_config() -> dict[str, Any]:
    path = _CONFIG_DIR / "app.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prompt(key: str) -> str:
    config = _load_config()
    if key not in config:
        raise KeyError(f"Prompt '{key}' not found in config/app.yaml")
    return config[key]


def get_config_section(key: str) -> dict[str, Any]:
    config = _load_config()
    if key not in config:
        raise KeyError(f"Section '{key}' not found in config/app.yaml")
    return config[key]
