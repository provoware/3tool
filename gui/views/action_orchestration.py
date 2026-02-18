from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6 import QtWidgets


def choose_project_root_dialog(parent, start_dir: str) -> Optional[Path]:
    chosen = QtWidgets.QFileDialog.getExistingDirectory(
        parent,
        "Projektordner wählen",
        start_dir,
    )
    if not chosen:
        return None
    project_root = Path(chosen).expanduser()
    if not project_root.exists() or not project_root.is_dir():
        QtWidgets.QMessageBox.warning(
            parent,
            "Projektordner ungültig",
            "Der ausgewählte Ordner ist nicht verfügbar oder ungültig.",
        )
        return None
    return project_root
