"""Einfache Smoke-Tests fuer grundlegende Importe."""

import pytest


def test_run_gui_importierbar() -> None:
    try:
        from videobatch_gui import run_gui
    except ImportError as exc:
        pytest.skip(f"GUI-Import nicht moeglich: {exc}")

    assert callable(run_gui)
