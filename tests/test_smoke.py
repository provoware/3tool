"""Einfache Smoke-Tests fuer grundlegende Importe."""


def test_run_gui_importierbar() -> None:
    from videobatch_gui import run_gui

    assert callable(run_gui)
