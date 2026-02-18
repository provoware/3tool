from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

from PySide6 import QtCore, QtWidgets


@dataclass
class ActionButtonSet:
    buttons: Dict[str, QtWidgets.QPushButton]
    wrappers: List[QtWidgets.QWidget]
    timer: QtCore.QTimer
    layout: QtWidgets.QGridLayout
    box: QtWidgets.QGroupBox


def wrap_button(
    button: QtWidgets.QPushButton, sublabel: str
) -> QtWidgets.QWidget:
    wrapper = QtWidgets.QFrame()
    wrapper.setProperty("actionTile", True)
    lay = QtWidgets.QVBoxLayout(wrapper)
    lay.setContentsMargins(10, 10, 10, 10)
    lay.setSpacing(6)
    button.setSizePolicy(
        QtWidgets.QSizePolicy.Policy.Expanding,
        QtWidgets.QSizePolicy.Policy.Fixed,
    )
    detail = QtWidgets.QLabel(sublabel)
    detail.setWordWrap(True)
    detail.setAlignment(
        QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
    )
    detail.setMinimumHeight(32)
    detail.setProperty("actionTileDetail", True)
    lay.addWidget(button)
    lay.addWidget(detail)
    return wrapper


def create_action_buttons(
    parent: QtWidgets.QWidget,
    on_timer_tick: Callable[[], None],
) -> ActionButtonSet:
    buttons = {
        "add_images": QtWidgets.QPushButton("Bilder wählen"),
        "add_audios": QtWidgets.QPushButton("Audios wählen"),
        "auto_pair": QtWidgets.QPushButton("Auto-Paaren"),
        "clear": QtWidgets.QPushButton("Alles löschen"),
        "undo": QtWidgets.QPushButton("Undo"),
        "save": QtWidgets.QPushButton("Projekt speichern"),
        "load": QtWidgets.QPushButton("Projekt laden"),
        "encode": QtWidgets.QPushButton("START"),
        "stop": QtWidgets.QPushButton("Stopp"),
        "wizard": QtWidgets.QPushButton("Geführter Start"),
    }
    buttons["encode"].setProperty("accentRole", "primaryAction")
    buttons["encode"].setProperty("readyPulse", "off")
    buttons["stop"].setEnabled(False)

    tips = {
        "add_images": "Bilder (Fotos) auswählen",
        "add_audios": "Audiodateien auswählen",
        "auto_pair": "Bilder und Audios automatisch koppeln",
        "clear": "Listen komplett leeren",
        "undo": "Letzte Änderung rückgängig machen",
        "save": "Aktuellen Stand speichern",
        "load": "Gespeichertes Projekt laden",
        "encode": "Encoding starten",
        "stop": "Aktuellen Vorgang abbrechen",
        "wizard": "Schritt-für-Schritt-Assistent öffnen",
    }
    subtitles: Iterable[Tuple[str, str]] = (
        ("add_images", "Bilder oder Ordner auswählen"),
        ("add_audios", "Audiodateien hinzufügen"),
        ("auto_pair", "Dateien automatisch koppeln"),
        ("wizard", "Assistent für Einsteiger öffnen"),
        ("clear", "Listen komplett leeren"),
        ("undo", "Letzten Schritt rückgängig"),
        ("save", "Projekt auf Platte sichern"),
        ("load", "Gespeichertes Projekt laden"),
        ("encode", "Videos jetzt erstellen"),
        ("stop", "Laufenden Vorgang abbrechen"),
    )
    for key, text in tips.items():
        buttons[key].setToolTip(text)

    wrappers = [wrap_button(buttons[key], label) for key, label in subtitles]
    for wrapper in wrappers:
        wrapper.setMinimumWidth(190)
        wrapper.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.MinimumExpanding,
        )

    layout = QtWidgets.QGridLayout()
    layout.setSpacing(4)
    layout.setContentsMargins(4, 4, 4, 4)

    box = QtWidgets.QGroupBox("Aktionen")
    box.setLayout(layout)

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
