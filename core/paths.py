from __future__ import annotations

from pathlib import Path


def user_data_dir() -> Path:
    return Path.home() / ".videobatchtool"


def config_dir() -> Path:
    return user_data_dir() / "config"


def log_dir() -> Path:
    return user_data_dir() / "logs"
