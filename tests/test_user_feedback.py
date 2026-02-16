from __future__ import annotations

import pytest

from core import user_feedback


def test_format_feedback_uses_expected_icons() -> None:
    assert user_feedback.format_feedback("info", "Hinweis") == "ℹ️ Hinweis"
    assert user_feedback.format_feedback("ok", "Fertig") == "✅ Fertig"
    assert user_feedback.format_feedback("warn", "Achtung") == "⚠️ Achtung"
    assert user_feedback.format_feedback("error", "Fehler") == "❌ Fehler"


def test_format_feedback_validates_level_and_message() -> None:
    with pytest.raises(ValueError):
        user_feedback.format_feedback("", "x")
    with pytest.raises(ValueError):
        user_feedback.format_feedback("unknown", "x")
    with pytest.raises(ValueError):
        user_feedback.format_feedback("info", "")


def test_print_debug_only_in_debug_mode(
    capsys: pytest.CaptureFixture[str],
) -> None:
    user_feedback.print_debug("sichtbar", True)
    user_feedback.print_debug("unsichtbar", False)

    captured = capsys.readouterr()
    assert "🐞 sichtbar" in captured.out
    assert "unsichtbar" not in captured.out


def test_print_debug_validates_debug_mode_type() -> None:
    with pytest.raises(TypeError):
        user_feedback.print_debug("x", "ja")  # type: ignore[arg-type]
