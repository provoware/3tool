from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Sequence

logger = logging.getLogger("VideoBatchTool")


def _coerce_to_int(value: object) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return int(stripped)
    return None


def parse_non_negative_int(
    value: object, field_name: str, default: int = 0
) -> int:
    """Parse integer values defensively for UI metrics."""
    if not isinstance(field_name, str) or not field_name.strip():
        raise ValueError("field_name muss ein nicht-leerer String sein")
    try:
        parsed_value = _coerce_to_int(value)
        if parsed_value is None:
            raise ValueError
        parsed = parsed_value
    except (TypeError, ValueError):
        logger.warning(
            "Ungueltiger Wert fuer '%s': %r. Nutze %s.",
            field_name,
            value,
            default,
        )
        return default
    if parsed < 0:
        logger.warning(
            "Negativer Wert fuer '%s': %s. Nutze %s.",
            field_name,
            parsed,
            default,
        )
        return default
    logger.debug("Wert fuer '%s' erfolgreich validiert: %s", field_name, parsed)
    return parsed


def clamp_progress(progress: object) -> int:
    """Clamp progress to 0..100 and log corrective actions."""
    safe_value = parse_non_negative_int(progress, "fortschritt")
    if safe_value > 100:
        logger.warning(
            "Fortschritt > 100 erkannt (%s). Begrenze auf 100.", safe_value
        )
        return 100
    logger.debug("Fortschritt validiert: %s", safe_value)
    return safe_value


def resolve_dashboard_columns(available_width: object) -> int:
    """Return a stable column count for dashboard cards."""
    try:
        width_value = _coerce_to_int(available_width)
        if width_value is None:
            raise ValueError
        usable_width = max(width_value, 1)
    except (TypeError, ValueError):
        logger.warning(
            "Dashboard-Reflow: verfuegbare Breite ist ungueltig (%r). Nutze 1 Spalte.",
            available_width,
        )
        return 1
    columns = max(1, min(3, usable_width // 250))
    logger.debug(
        "Dashboard-Reflow berechnet: %s Spalten bei %s px",
        columns,
        usable_width,
    )
    return columns


def format_human_size(path: Path) -> str:
    """Human readable file size with defensive fallback."""
    if not isinstance(path, Path):
        raise TypeError("path muss vom Typ pathlib.Path sein")
    try:
        size = path.stat().st_size
    except OSError as exc:
        logger.warning(
            "Dateigroesse konnte nicht gelesen werden (%s): %s", path, exc
        )
        return "?"
    units: Iterable[str] = ("B", "KB", "MB", "GB")
    unit_list = list(units)
    value = float(size)
    idx = 0
    while value >= 1024 and idx < len(unit_list) - 1:
        value /= 1024
        idx += 1
    result = f"{value:.1f} {unit_list[idx]}"
    logger.debug("Dateigroesse formatiert: %s -> %s", path, result)
    return result


def normalize_layout_width(available_width: object) -> int:
    """Normalize width values for responsive layouts."""
    width = parse_non_negative_int(
        available_width,
        "layout_breite",
        default=0,
    )
    logger.debug("Layout-Breite validiert: %s", width)
    return width


def resolve_action_layout_columns(
    *,
    available_width: object,
    minimum_widths: Sequence[int],
    spacing: int,
    margin_left: int,
    margin_right: int,
    button_label_width: int,
    content_min_width: object = 0,
) -> tuple[int, int]:
    """Resolve responsive action-grid columns with strict input checks."""
    safe_width = normalize_layout_width(available_width)
    safe_spacing = parse_non_negative_int(spacing, "layout_abstand", default=0)
    safe_margin_left = parse_non_negative_int(
        margin_left,
        "layout_rand_links",
        default=0,
    )
    safe_margin_right = parse_non_negative_int(
        margin_right,
        "layout_rand_rechts",
        default=0,
    )
    safe_button_label_width = parse_non_negative_int(
        button_label_width,
        "button_label_breite",
        default=190,
    )
    sanitized_min_widths = [
        parse_non_negative_int(value, "button_min_breite", default=190)
        for value in minimum_widths
    ]
    safe_content_min_width = parse_non_negative_int(
        content_min_width,
        "button_content_min_breite",
        default=0,
    )
    usable_width = max(
        safe_width - safe_margin_left - safe_margin_right,
        240,
    )
    dynamic_min_width = max(160, safe_button_label_width + 60)
    min_cell_width = max(
        max(sanitized_min_widths, default=190),
        dynamic_min_width,
        safe_content_min_width,
    )
    max_columns = 4 if usable_width >= 1100 else 3
    columns = max(
        1,
        min(
            max_columns,
            usable_width // max(min_cell_width + safe_spacing, 1),
        ),
    )
    logger.debug(
        "Action-Reflow: width=%s usable=%s columns=%s/%s",
        safe_width,
        usable_width,
        columns,
        max_columns,
    )
    return columns, max_columns


def resolve_action_cell_min_width(
    *,
    minimum_widths: Sequence[object],
    size_hint_widths: Sequence[object],
    minimum_hint_widths: Sequence[object],
    button_label_width: object,
) -> int:
    """Resolve a content-aware action cell width from widget size hints."""
    safe_label_width = parse_non_negative_int(
        button_label_width,
        "button_label_breite",
        default=190,
    )
    parsed_minimums = [
        parse_non_negative_int(value, "button_min_breite", default=190)
        for value in minimum_widths
    ]
    parsed_hints = [
        parse_non_negative_int(value, "button_size_hint", default=0)
        for value in size_hint_widths
    ]
    parsed_min_hints = [
        parse_non_negative_int(
            value,
            "button_min_size_hint",
            default=0,
        )
        for value in minimum_hint_widths
    ]

    explicit_min_width = max(parsed_minimums, default=190)
    content_hint_width = max(parsed_hints + parsed_min_hints, default=0)
    label_based_width = max(160, safe_label_width + 60)
    cell_width = max(explicit_min_width, content_hint_width, label_based_width)
    logger.debug(
        "Action-Reflow Breite: min=%s hint=%s label=%s => %s",
        explicit_min_width,
        content_hint_width,
        label_based_width,
        cell_width,
    )
    return cell_width


def compute_workflow_min_size(
    *,
    font_size: object,
    dpi_scale: object,
    available_width: object,
    available_height: object,
    layout_columns: object,
    splitter_handle_width: object,
    splitter_count: object,
    section_min_width: object,
    section_min_height: object,
    density_multiplier: object = 1.0,
) -> tuple[int, int]:
    """Compute adaptive workflow minimum size (DPI + font aware)."""
    safe_font = parse_non_negative_int(font_size, "schriftgroesse", default=13)
    safe_font = max(10, min(36, int(safe_font)))
    try:
        parsed_dpi_scale = float(dpi_scale)
    except (TypeError, ValueError):
        parsed_dpi_scale = 1.0
    safe_dpi_scale = max(parsed_dpi_scale, 1.0)
    font_scale = max(1.0, safe_font / 13.0)
    try:
        parsed_density = float(density_multiplier)
    except (TypeError, ValueError):
        parsed_density = 1.0
    safe_density = min(max(parsed_density, 0.85), 1.9)
    scale = max(safe_dpi_scale, font_scale) * safe_density

    safe_columns = max(
        1,
        parse_non_negative_int(layout_columns, "workflow_spalten", default=1),
    )
    safe_section_min_width = max(
        280,
        parse_non_negative_int(
            section_min_width,
            "workflow_min_breite",
            default=280,
        ),
    )
    safe_section_min_height = max(
        220,
        parse_non_negative_int(
            section_min_height,
            "workflow_min_hoehe",
            default=220,
        ),
    )
    safe_available_width = max(
        parse_non_negative_int(
            available_width, "workflow_verfuegbare_breite", 480
        ),
        480,
    )
    safe_handle_width = parse_non_negative_int(
        splitter_handle_width,
        "splitter_handle_breite",
        default=0,
    )
    safe_splitter_count = parse_non_negative_int(
        splitter_count,
        "splitter_anzahl",
        default=0,
    )
    usable_width = max(
        safe_available_width - (safe_handle_width * safe_splitter_count),
        safe_section_min_width,
    )
    max_per_section = max(
        safe_section_min_width,
        int(usable_width / safe_columns),
    )
    dynamic_width = int(safe_section_min_width * scale)
    min_width = min(
        max_per_section,
        max(safe_section_min_width, dynamic_width),
    )

    safe_available_height = max(
        parse_non_negative_int(
            available_height,
            "workflow_verfuegbare_hoehe",
            360,
        ),
        360,
    )
    max_per_section_h = max(
        safe_section_min_height, int(safe_available_height / 2)
    )
    dynamic_height = int(safe_section_min_height * scale)
    min_height = min(
        max_per_section_h,
        max(safe_section_min_height, dynamic_height),
    )
    logger.debug(
        "Workflow-Mindestgroesse: %sx%s (scale=%.2f, density=%.2f, columns=%s)",
        min_width,
        min_height,
        scale,
        safe_density,
        safe_columns,
    )
    return min_width, min_height
