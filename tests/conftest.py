from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def qapp():
    try:
        from PySide6 import QtWidgets
    except ImportError as exc:
        pytest.skip(f"PySide6 fehlt: {exc}")
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    yield app


@pytest.fixture(scope="session")
def gui_runtime_error() -> str | None:
    try:
        importlib.import_module("videobatch_gui")
    except ImportError as exc:
        return str(exc)
    return None


@pytest.fixture(scope="session")
def gui_runtime_available(gui_runtime_error: str | None) -> bool:
    return gui_runtime_error is None
