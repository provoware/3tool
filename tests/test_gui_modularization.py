from pathlib import Path

from core.gui_logic import (clamp_progress, compute_workflow_min_size,
                            format_human_size, normalize_layout_width,
                            parse_non_negative_int,
                            resolve_action_cell_min_width,
                            resolve_action_layout_columns,
                            resolve_dashboard_columns)
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


def test_action_cell_min_width_uses_content_hints() -> None:
    cell_width = resolve_action_cell_min_width(
        minimum_widths=[180, 200],
        size_hint_widths=[220, 310],
        minimum_hint_widths=[190, 205],
        button_label_width=240,
    )
    assert cell_width >= 310


def test_action_layout_spalten_validiert() -> None:
    columns, max_columns = resolve_action_layout_columns(
        available_width="1200",
        minimum_widths=[180, -1, 240],
        spacing=8,
        margin_left=12,
        margin_right=12,
        button_label_width=260,
        content_min_width=340,
    )
    assert max_columns == 4
    assert columns >= 1


def test_workflow_min_size_ist_robust() -> None:
    min_width, min_height = compute_workflow_min_size(
        font_size="14",
        dpi_scale="1.5",
        available_width=1280,
        available_height=800,
        layout_columns=3,
        splitter_handle_width=6,
        splitter_count=2,
        section_min_width=300,
        section_min_height=260,
        density_multiplier=1.2,
    )
    assert min_width >= 300
    assert min_height >= 260


def test_layout_width_normalisierung() -> None:
    assert normalize_layout_width("500") == 500
    assert normalize_layout_width("") == 0
