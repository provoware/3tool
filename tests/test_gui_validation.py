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
