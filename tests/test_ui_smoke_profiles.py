import importlib

import pytest


SCREEN_CASES = [
    (800, 600),
    (1366, 768),
    (1920, 1080),
]
THEME_CASES = ["Modern", "Hochkontrast Dunkel"]


def _import_gui_module():
    return importlib.import_module("videobatch_gui")


@pytest.mark.parametrize("width,height", SCREEN_CASES)
@pytest.mark.parametrize("theme", THEME_CASES)
def test_main_window_ui_smoke_profiles(
    request,
    gui_runtime_available,
    gui_runtime_error,
    width: int,
    height: int,
    theme: str,
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert (
            "libGL.so.1" in gui_runtime_error
            or "libEGL.so.1" in gui_runtime_error
        )
        return

    qtbot = request.getfixturevalue("qtbot")
    videobatch_gui = _import_gui_module()

    win = videobatch_gui.MainWindow()
    qtbot.addWidget(win)
    win._set_font(18)
    win._apply_theme(theme)
    win.resize(width, height)
    win.show()
    qtbot.wait(50)

    assert win.width() >= width
    assert win.height() >= height
    assert win.btn_encode.isVisible()
    assert win.dashboard.isVisible()
    assert len(win.workflow_splitters) == 3
    assert all(splitter.count() >= 2 for splitter in win.workflow_splitters)
