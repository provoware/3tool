from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

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
