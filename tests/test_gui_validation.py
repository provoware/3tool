import importlib
import sys

from core import launcher_checks


def _import_gui_module():
    return importlib.import_module("videobatch_gui")


def test_gui_runtime_reports_missing_libgl_if_unavailable(gui_runtime_error):
    if gui_runtime_error is None:
        result = launcher_checks.check_gui_runtime(sys.executable)
        assert result.ok
        return

    result = launcher_checks.check_gui_runtime(sys.executable)
    assert not result.ok
    assert "GUI-Import fehlgeschlagen" in result.detail
    assert "libGL.so.1" in result.detail
    assert result.fix_hint


def test_validate_image_fields_marks_invalid(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.image_edit.setText("/tmp/not-existing-image.jpg")
    win.validate_image_fields()

    assert "#ffd6d6" in win.image_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_validate_audio_fields_marks_invalid(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win.audio_edit.setText("/tmp/not-existing-audio.mp3")
    win.validate_audio_fields()

    assert "#ffd6d6" in win.audio_edit.styleSheet()
    assert "existiert nicht" in win.validation_msg.text()


def test_dashboard_counts_are_clamped(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_counts(2, 5, -1)

    assert dashboard.total_label.text() == "2"
    assert dashboard.done_label.text() == "2"
    assert dashboard.err_label.text() == "0"


def test_dashboard_progress_is_limited_to_100(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    dashboard = videobatch_gui.InfoDashboard()
    qtbot.addWidget(dashboard)

    dashboard.set_progress(160)

    assert dashboard.progress.value() == 100
    assert dashboard.progress_value.text() == "100%"


def test_action_buttons_reflow_to_two_columns_on_medium_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width=500)

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0, 1}


def test_action_buttons_reflow_to_single_column_on_small_width(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()
    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)

    win._reflow_action_buttons(available_width=240)

    positions = []
    for idx in range(win.top_buttons_layout.count()):
        row, col, _, _ = win.top_buttons_layout.getItemPosition(idx)
        positions.append((row, col))
    used_columns = {col for _, col in positions}
    assert used_columns == {0}
