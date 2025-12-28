import os

import pytest

import videobatch_launcher
from core import launcher_checks


def _build_wizard(monkeypatch):
    Wizard, QtWidgets, _, _ = videobatch_launcher.build_wizard()
    monkeypatch.setattr(Wizard, "_start_check", lambda self: None)
    return Wizard, QtWidgets


def test_wizard_handle_results_updates_buttons(monkeypatch, qapp):
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


def test_wizard_toggle_debug_signal_updates_env(monkeypatch, qapp):
    monkeypatch.setattr(videobatch_launcher, "setup_logging", lambda _: None)
    os.environ.pop("VT_DEBUG", None)
    Wizard, _ = _build_wizard(monkeypatch)
    wizard = Wizard()
    QtCore = pytest.importorskip("PySide6.QtCore")
    QtTest = pytest.importorskip("PySide6.QtTest")

    QtTest.QTest.mouseClick(wizard.debug_check, QtCore.Qt.LeftButton)

    assert os.environ.get("VT_DEBUG") == "1"


def test_wizard_fix_results_restarts_check(monkeypatch, qapp):
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
