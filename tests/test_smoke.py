"""Einfache Smoke-Tests fuer grundlegende Importe."""

import sys

from core import launcher_checks


def test_run_gui_importierbar() -> None:
    try:
        from videobatch_gui import run_gui
    except ImportError as exc:
        result = launcher_checks.check_gui_runtime(sys.executable)
        assert not result.ok
        assert "GUI-Import fehlgeschlagen" in result.detail
        assert str(exc) in result.detail
        return

    assert callable(run_gui)
