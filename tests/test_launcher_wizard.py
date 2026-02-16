import os

import pytest

import videobatch_launcher
from core import launcher_checks


def _build_wizard(monkeypatch):
    Wizard, QtWidgets, _, _ = videobatch_launcher.build_wizard()
    monkeypatch.setattr(Wizard, "_start_check", lambda self: None)
    return Wizard, QtWidgets


def test_wizard_handle_results_updates_buttons(
    monkeypatch,
    request,
    gui_runtime_available,
    gui_runtime_error,
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    request.getfixturevalue("qapp")
    Wizard, _ = _build_wizard(monkeypatch)
    wizard = Wizard()

    results = [
        launcher_checks.CheckResult(
            key="python",
            title="Python",
            ok=True,
            detail="ok",
            blocking=True,
        ),
        launcher_checks.CheckResult(
            key="internet",
            title="Internet",
            ok=False,
            detail="offline",
            blocking=False,
        ),
    ]

    wizard._handle_results(results)

    assert wizard.btn_fix.isEnabled()
    assert wizard.btn_start.isEnabled()


def test_wizard_toggle_debug_signal_updates_env(
    monkeypatch,
    request,
    gui_runtime_available,
    gui_runtime_error,
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    request.getfixturevalue("qapp")
    monkeypatch.setattr(videobatch_launcher, "setup_logging", lambda _: None)
    os.environ.pop("VT_DEBUG", None)
    Wizard, _ = _build_wizard(monkeypatch)
    wizard = Wizard()
    QtCore = pytest.importorskip("PySide6.QtCore")
    QtTest = pytest.importorskip("PySide6.QtTest")

    QtTest.QTest.mouseClick(wizard.debug_check, QtCore.Qt.LeftButton)

    assert os.environ.get("VT_DEBUG") == "1"


def test_wizard_fix_results_restarts_check(
    monkeypatch,
    request,
    gui_runtime_available,
    gui_runtime_error,
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    request.getfixturevalue("qapp")
    Wizard, _ = _build_wizard(monkeypatch)
    wizard = Wizard()
    started = {"called": False}

    def _start_check():
        started["called"] = True

    wizard._start_check = _start_check
    results = [
        launcher_checks.RepairResult(
            key="packages",
            title="Python-Pakete",
            ok=False,
            detail="Kein Internet, Installation übersprungen.",
            skipped_offline=True,
        )
    ]

    wizard._handle_fix_results(results)

    assert started["called"]
    assert "Kein Internet" in wizard.info.toPlainText()


def test_wizard_render_results_contains_next_steps(
    monkeypatch,
    request,
    gui_runtime_available,
    gui_runtime_error,
):
    if not gui_runtime_available:
        assert gui_runtime_error is not None
        assert "libGL.so.1" in gui_runtime_error
        return

    request.getfixturevalue("qapp")
    Wizard, _ = _build_wizard(monkeypatch)
    wizard = Wizard()
    results = [
        launcher_checks.CheckResult(
            key="python",
            title="Python",
            ok=False,
            detail="zu alt",
            fix_hint="Python aktualisieren",
            blocking=True,
        )
    ]

    html, pct = wizard._render_results(results)

    assert "Naechste Schritte" in html
    assert "Start noch nicht bereit" in html
    assert "Begriffe einfach erklaert" in html
    assert "Schnelle Befehle (Terminal)" in html
    assert pct == 0
