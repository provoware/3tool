from __future__ import annotations

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)

from gui.views.main_window_view import create_action_buttons  # noqa: E402


def test_create_action_buttons_builds_expected_controls(qtbot):
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    state = {"ticks": 0}

    def _tick() -> None:
        state["ticks"] += 1

    action_set = create_action_buttons(parent, on_timer_tick=_tick)
    assert action_set.box.title() == "Aktionen"
    assert "encode" in action_set.buttons
    assert action_set.buttons["encode"].text() == "START"
    assert len(action_set.wrappers) == 10
