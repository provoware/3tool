from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


def make_project_relative(path: str, project_root: Optional[Path]) -> str:
    if not path:
        return path
    if not project_root:
        return path
    file_path = Path(path).expanduser()
    try:
        return str(file_path.relative_to(project_root))
    except ValueError:
        return str(file_path)


def resolve_project_path(
    path: str, project_root: Optional[Path], project_file: Optional[Path]
) -> str:
    if not path:
        return path
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return str(candidate)
    base = project_root or (project_file.parent if project_file else None)
    if base:
        return str(base / candidate)
    return str(candidate)


def build_project_payload(
    pairs: list[Any], settings: dict[str, Any], project_root: Optional[Path]
) -> dict[str, Any]:
    return {
        "pairs": [
            {
                "image": make_project_relative(pair.image_path, project_root),
                "audio": make_project_relative(
                    pair.audio_path or "", project_root
                ),
                "output": make_project_relative(pair.output, project_root),
            }
            for pair in pairs
        ],
        "settings": settings,
    }


def save_project_file(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_project_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
