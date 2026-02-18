from pathlib import Path

from core.gui_logic import (
    clamp_progress,
    format_human_size,
    parse_non_negative_int,
    resolve_dashboard_columns,
)
from gui.controllers.actions import build_initial_state


def test_gui_logic_validierung_und_clamp() -> None:
    assert parse_non_negative_int("3", "feld") == 3
    assert parse_non_negative_int("x", "feld") == 0
    assert clamp_progress(150) == 100


def test_dashboard_reflow_spalten_robust() -> None:
    assert resolve_dashboard_columns(900) == 3
    assert resolve_dashboard_columns("ungueltig") == 1


def test_format_human_size_defensiv(tmp_path: Path) -> None:
    file_path = tmp_path / "a.bin"
    file_path.write_bytes(b"x" * 2048)
    assert format_human_size(file_path).endswith("KB")


def test_main_window_state_initialisiert() -> None:
    state = build_initial_state(Path("/tmp/a"), Path("/tmp/b"))
    assert state.last_image_dir == Path("/tmp/a")
    assert state.last_audio_dir == Path("/tmp/b")
