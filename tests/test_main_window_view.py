from __future__ import annotations

import importlib

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)
QtCore = pytest.importorskip("PySide6.QtCore", exc_type=ImportError)

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


def test_table_displays_long_paths_with_wrap_and_without_elide(
    qtbot, qapp, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    videobatch_gui = importlib.import_module("videobatch_gui")
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.show()

    long_image_path = "/tmp/" + ("sehr_langer_bildpfad_" * 14) + ".jpg"
    long_audio_path = "/tmp/" + ("sehr_langer_audiopfad_" * 14) + ".mp3"
    row_item = videobatch_gui.PairItem(long_image_path, long_audio_path)
    row_item.update_duration()
    row_item.validate()

    win.model.add_pairs([row_item])
    win._resize_columns()
    qapp.processEvents()

    assert win.table.wordWrap() is True
    assert win.table.textElideMode() == QtCore.Qt.TextElideMode.ElideNone
    model_idx = win.model.index(0, 2)
    assert (
        win.model.data(model_idx, QtCore.Qt.ItemDataRole.DisplayRole)
        == long_image_path
    )
    assert win.table.rowHeight(0) > 0

    win.resize(1700, 900)
    qapp.processEvents()
    win._update_table_horizontal_scroll_policy()
    assert (
        win.table.horizontalScrollBarPolicy()
        == QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )

    win.resize(540, 700)
    qapp.processEvents()
    win._update_table_horizontal_scroll_policy()
    assert (
        win.table.horizontalScrollBarPolicy()
        == QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )
