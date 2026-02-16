from __future__ import annotations

from typing import Final

_STATUS_ICONS: Final[dict[str, str]] = {
    "info": "ℹ️",
    "ok": "✅",
    "warn": "⚠️",
    "error": "❌",
    "debug": "🐞",
}


def _validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} muss ein String sein.")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} darf nicht leer sein.")
    return cleaned


def format_feedback(level: str, message: str) -> str:
    normalized_level = _validate_text(level, "level").lower()
    if normalized_level not in _STATUS_ICONS:
        allowed = ", ".join(sorted(_STATUS_ICONS))
        raise ValueError(
            f"Unbekanntes Feedback-Level '{normalized_level}'. Erlaubt: {allowed}"
        )
    validated_message = _validate_text(message, "message")
    return f"{_STATUS_ICONS[normalized_level]} {validated_message}"


def print_feedback(level: str, message: str) -> None:
    print(format_feedback(level, message))


def print_debug(message: str, debug_mode: bool) -> None:
    validated_debug_mode = debug_mode
    if not isinstance(validated_debug_mode, bool):
        raise TypeError("debug_mode muss ein bool sein.")
    if validated_debug_mode:
        print_feedback("debug", message)
