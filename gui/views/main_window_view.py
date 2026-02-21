from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

from PySide6 import QtCore, QtWidgets


@dataclass
class ActionButtonSet:
    buttons: Dict[str, QtWidgets.QPushButton]
    wrappers: List[QtWidgets.QWidget]
    timer: QtCore.QTimer
    layout: QtWidgets.QGridLayout
    box: QtWidgets.QGroupBox


_BUTTON_CONFIG: Dict[str, Dict[str, str]] = {
    "add_images": {
        "label": "Bilder wählen",
        "tooltip": "Bilder (Fotos) auswählen",
        "subtitle": "Bilder oder Ordner auswählen",
        "role": "support",
    },
    "add_audios": {
        "label": "Audios wählen",
        "tooltip": "Audiodateien auswählen",
        "subtitle": "Audiodateien hinzufügen",
        "role": "support",
    },
    "auto_pair": {
        "label": "Auto-Paaren",
        "tooltip": "Bilder und Audios automatisch koppeln",
        "subtitle": "Dateien automatisch koppeln",
        "role": "secondary",
    },
    "wizard": {
        "label": "Geführter Start",
        "tooltip": "Schritt-für-Schritt-Assistent öffnen",
        "subtitle": "Assistent für Einsteiger öffnen",
        "role": "secondary",
    },
    "clear": {
        "label": "Alles löschen",
        "tooltip": "Listen komplett leeren",
        "subtitle": "Listen komplett leeren",
        "role": "danger",
    },
    "undo": {
        "label": "Undo",
        "tooltip": "Letzte Änderung rückgängig machen",
        "subtitle": "Letzten Schritt rückgängig",
        "role": "secondary",
    },
    "redo": {
        "label": "Redo",
        "tooltip": "Rückgängig rückgängig machen",
        "subtitle": "Rückgängig wiederherstellen",
        "role": "secondary",
    },
    "save": {
        "label": "Projekt speichern",
        "tooltip": "Aktuellen Stand speichern",
        "subtitle": "Projekt auf Platte sichern",
        "role": "secondary",
    },
    "load": {
        "label": "Projekt laden",
        "tooltip": "Gespeichertes Projekt laden",
        "subtitle": "Gespeichertes Projekt laden",
        "role": "secondary",
    },
    "encode": {
        "label": "START",
        "tooltip": "Encoding starten",
        "subtitle": "Videos jetzt erstellen",
        "role": "primary",
    },
    "stop": {
        "label": "Stopp",
        "tooltip": "Aktuellen Vorgang abbrechen",
        "subtitle": "Laufenden Vorgang abbrechen",
        "role": "danger",
    },
}

_PRIMARY_ACTION_KEYS: Tuple[str, ...] = (
    "add_images",
    "add_audios",
    "auto_pair",
    "wizard",
    "save",
    "load",
    "clear",
    "stop",
    "encode",
)

_SECONDARY_ACTION_KEYS: Tuple[str, ...] = ("undo", "redo")


def _configure_action_button(
    button: QtWidgets.QPushButton,
    *,
    key: str,
    tooltip: str,
    role: str,
) -> None:
    button.setProperty("buttonRole", role)
    button.setProperty("actionButton", True)
    button.setObjectName(f"action_button_{key}")
    button.setToolTip(tooltip)
    button.setAccessibleName(button.text())
    button.setAccessibleDescription(f"Aktion: {tooltip}")
    button.setMinimumHeight(46)
    button.setMinimumWidth(184)
    button.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )


def wrap_button(
    button: QtWidgets.QPushButton, sublabel: str
) -> QtWidgets.QWidget:
    wrapper = QtWidgets.QFrame()
    wrapper.setProperty("actionTile", True)
    lay = QtWidgets.QVBoxLayout(wrapper)
    lay.setContentsMargins(10, 10, 10, 10)
    lay.setSpacing(8)
    detail = QtWidgets.QLabel(sublabel)
    detail.setWordWrap(True)
    detail.setAlignment(
        QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
    )
    detail.setMinimumHeight(34)
    detail.setProperty("actionTileDetail", True)
    detail.setAccessibleDescription(f"Zusatzinfo: {sublabel}")
    lay.addWidget(button)
    lay.addWidget(detail)
    return wrapper


def create_action_buttons(
    parent: QtWidgets.QWidget,
    on_timer_tick: Callable[[], None],
) -> ActionButtonSet:
    buttons = {
        key: QtWidgets.QPushButton(config["label"])
        for key, config in _BUTTON_CONFIG.items()
    }
    for key, button in buttons.items():
        config = _BUTTON_CONFIG[key]
        _configure_action_button(
            button,
            key=key,
            tooltip=config["tooltip"],
            role=config["role"],
        )
    buttons["encode"].setProperty("accentRole", "primaryAction")
    buttons["encode"].setProperty("readyPulse", "off")
    buttons["stop"].setEnabled(False)

    wrappers = [
        wrap_button(buttons[key], _BUTTON_CONFIG[key]["subtitle"])
        for key in _PRIMARY_ACTION_KEYS
    ]
    for wrapper in wrappers:
        wrapper.setMinimumWidth(200)
        wrapper.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )

    secondary_wrappers = [
        wrap_button(buttons[key], _BUTTON_CONFIG[key]["subtitle"])
        for key in _SECONDARY_ACTION_KEYS
    ]
    for wrapper in secondary_wrappers:
        wrapper.setMinimumWidth(200)
        wrapper.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

    layout = QtWidgets.QGridLayout()
    layout.setSpacing(8)
    layout.setContentsMargins(6, 6, 6, 6)

    secondary_box = QtWidgets.QGroupBox("Verlauf")
    secondary_layout = QtWidgets.QGridLayout(secondary_box)
    secondary_layout.setSpacing(8)
    secondary_layout.setContentsMargins(6, 6, 6, 6)
    for index, wrapper in enumerate(secondary_wrappers):
        secondary_layout.addWidget(wrapper, 0, index)
        secondary_layout.setColumnStretch(index, 1)

    box = QtWidgets.QGroupBox("Aktionen")
    box_layout = QtWidgets.QVBoxLayout(box)
    box_layout.setContentsMargins(6, 6, 6, 6)
    box_layout.setSpacing(10)
    box_layout.addLayout(layout)
    box_layout.addWidget(secondary_box)

    timer = QtCore.QTimer(parent)
    timer.setInterval(500)
    timer.timeout.connect(on_timer_tick)

    return ActionButtonSet(
        buttons=buttons,
        wrappers=wrappers,
        timer=timer,
        layout=layout,
        box=box,
    )
