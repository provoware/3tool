from __future__ import annotations


def test_error_banner_shows_and_clears(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    from PySide6 import QtWidgets

    from gui.widgets.feedback import ErrorBanner

    qtbot = request.getfixturevalue("qtbot")
    banner = ErrorBanner()
    qtbot.addWidget(banner)

    banner.show_error("Validierungsfehler", "Audio fehlt")

    assert banner.isVisible()
    assert "Nächster Schritt" in banner.findChildren(QtWidgets.QLabel)[1].text()

    banner.clear_message()

    assert not banner.isVisible()


def test_warning_badge_shows_and_clears(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    from gui.widgets.feedback import WarningBadge

    qtbot = request.getfixturevalue("qtbot")
    badge = WarningBadge()
    qtbot.addWidget(badge)

    badge.show_warning("Bitte Ausgabeordner prüfen")

    assert badge.isVisible()
    assert badge.text().startswith("Hinweis:")

    badge.clear_warning()

    assert not badge.isVisible()


def test_success_toast_auto_hides(
    request, gui_runtime_available, gui_runtime_error
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        return

    from gui.widgets.feedback import SuccessToast

    qtbot = request.getfixturevalue("qtbot")
    toast = SuccessToast()
    qtbot.addWidget(toast)

    toast.show_message("Alles fertig", timeout_ms=1200)

    assert toast.isVisible()
    assert toast.text().startswith("OK:")

    qtbot.wait(1300)

    assert not toast.isVisible()
