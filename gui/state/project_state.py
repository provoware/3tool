from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtCore


def get_project_root(settings: QtCore.QSettings) -> Optional[Path]:
    value = settings.value("ui/project_root", "", str)
    if not value:
        return None
    root = Path(value).expanduser()
    if root.exists() and root.is_dir():
        return root
    return None


def set_project_root(
    settings: QtCore.QSettings,
    path: Path,
    *,
    log_callback,
) -> bool:
    if not isinstance(path, Path) or not path.exists() or not path.is_dir():
        return False
    settings.setValue("ui/project_root", str(path))
    settings.setValue("ui/last_project_root_dir", str(path))
    log_callback(f"Projektordner gesetzt: {path}")
    return True


def set_last_project_path(
    settings: QtCore.QSettings,
    state,
    path: str,
) -> bool:
    if not isinstance(path, str) or not path.strip():
        return False
    project_path = Path(path).expanduser()
    settings.setValue("ui/last_project_path", str(project_path))
    settings.setValue("ui/last_project_dir", str(project_path.parent))
    state.last_project_file = project_path
    return True


def get_project_start_dir(
    settings: QtCore.QSettings,
    project_dir_text: str,
    *,
    last_dir_resolver,
) -> str:
    default_dir = (project_dir_text or "").strip()
    if default_dir:
        stored = Path(default_dir).expanduser()
        if stored.exists():
            return str(stored)
    return last_dir_resolver("ui/last_project_dir", Path.cwd())
