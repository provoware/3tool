from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    used_dir: Path
    output_dir: Path
    project_dir: Path
    downloads_dir: Path

    def __post_init__(self) -> None:
        for attr_name in (
            "used_dir",
            "output_dir",
            "project_dir",
            "downloads_dir",
        ):
            value = getattr(self, attr_name)
            if not isinstance(value, Path):
                raise TypeError(f"{attr_name} muss ein pathlib.Path sein")
