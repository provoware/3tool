from __future__ import annotations

import logging
from typing import Final

LAUNCHER_THEME_PALETTES: Final[dict[str, dict[str, str]]] = {
    "Hell": {
        "window": "#f4f6fb",
        "window_text": "#111111",
        "base": "#ffffff",
        "text": "#111111",
        "button": "#e6ebf5",
        "button_text": "#111111",
    },
    "Dunkel": {
        "window": "#1f1f1f",
        "window_text": "#f2f2f2",
        "base": "#2b2b2b",
        "text": "#f2f2f2",
        "button": "#333333",
        "button_text": "#f2f2f2",
    },
    "Hoher Kontrast": {
        "window": "#000000",
        "window_text": "#ffffff",
        "base": "#000000",
        "text": "#ffffff",
        "button": "#000000",
        "button_text": "#ffffff",
    },
}


def validate_launcher_theme_name(theme_name: str) -> str:
    if not isinstance(theme_name, str):
        raise TypeError("theme_name muss ein String sein.")
    cleaned = theme_name.strip()
    if not cleaned:
        raise ValueError("theme_name darf nicht leer sein.")
    if cleaned not in LAUNCHER_THEME_PALETTES:
        allowed = ", ".join(sorted(LAUNCHER_THEME_PALETTES))
        raise ValueError(
            f"Unbekanntes Launcher-Theme '{cleaned}'. Erlaubt: {allowed}"
        )
    return cleaned


def resolve_launcher_theme(theme_name: str) -> dict[str, str]:
    valid_name = validate_launcher_theme_name(theme_name)
    palette = LAUNCHER_THEME_PALETTES[valid_name]
    required_keys = {
        "window",
        "window_text",
        "base",
        "text",
        "button",
        "button_text",
    }
    if set(palette) != required_keys:
        raise ValueError(
            "Theme-Definition unvollständig. Erwartete Schlüssel: "
            + ", ".join(sorted(required_keys))
        )
    return dict(palette)


def log_theme_selection(
    theme_name: str,
    logger: logging.Logger | None = None,
) -> str:
    valid_name = validate_launcher_theme_name(theme_name)
    active_logger = logger or logging.getLogger(__name__)
    active_logger.info("Launcher-Theme gesetzt: %s", valid_name)
    return valid_name
