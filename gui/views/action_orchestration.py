from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PySide6 import QtWidgets

from gui.controllers.actions import (resolve_text,
                                     validate_project_root_candidate)


def choose_project_root_dialog(
    parent,
    start_dir: str,
    texts: Optional[Dict[str, str]] = None,
) -> Optional[Path]:
    ui_texts = texts or {}
    title = resolve_text(
        ui_texts,
        "dialog.project_root.title",
        "Projektordner wählen",
    )
    chosen = QtWidgets.QFileDialog.getExistingDirectory(
        parent, title, start_dir
    )
    if not chosen:
        return None
    project_root = Path(chosen).expanduser()
    if not validate_project_root_candidate(project_root):
        QtWidgets.QMessageBox.warning(
            parent,
            resolve_text(
                ui_texts,
                "error.project_root.invalid_title",
                "Projektordner ungültig",
            ),
            resolve_text(
                ui_texts,
                "error.project_root.invalid_body",
                "Der ausgewählte Ordner ist nicht verfügbar oder ungültig.",
            ),
        )
        return None
    return project_root
