import importlib

import pytest


try:
    videobatch_gui = importlib.import_module("videobatch_gui")
except ImportError as exc:  # pragma: no cover - depends on system GUI libs
    pytestmark = pytest.mark.skip(reason=f"GUI-Abhängigkeit fehlt: {exc}")


def _new_mainwindow(qtbot):
    window = videobatch_gui.MainWindow()
    qtbot.addWidget(window)
    return window


def test_validate_image_fields_marks_invalid(qtbot):
    win = _new_mainwindow(qtbot)
    win.image_edit.setText("/tmp/not-existing-image.jpg")
    win.validate_image_fields()

    assert "#ffd6d6" in win.image_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_validate_audio_fields_marks_invalid(qtbot):
    win = _new_mainwindow(qtbot)
    win.audio_edit.setText("/tmp/not-existing-audio.mp3")
    win.validate_audio_fields()

    assert "#ffd6d6" in win.audio_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_dashboard_counts_are_clamped(qtbot):
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_counts(2, 5, -1)

    assert dashboard.total_label.text() == "2"
    assert dashboard.done_label.text() == "2"
    assert dashboard.err_label.text() == "0"


def test_dashboard_progress_is_limited_to_100(qtbot):
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_progress(160)

    assert dashboard.progress.value() == 100
    assert dashboard.progress_value.text() == "100%"
