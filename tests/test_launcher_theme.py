import logging

import pytest

from core import launcher_theme


def test_validate_launcher_theme_name_accepts_known_theme() -> None:
    assert launcher_theme.validate_launcher_theme_name("Dunkel") == "Dunkel"


def test_validate_launcher_theme_name_rejects_unknown_theme() -> None:
    with pytest.raises(ValueError):
        launcher_theme.validate_launcher_theme_name("Retro")


def test_resolve_launcher_theme_returns_required_keys() -> None:
    palette = launcher_theme.resolve_launcher_theme("Hoher Kontrast")
    assert set(palette) == {
        "window",
        "window_text",
        "base",
        "text",
        "button",
        "button_text",
    }


def test_log_theme_selection_logs_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("tests.launcher_theme")
    with caplog.at_level(logging.INFO, logger=logger.name):
        selected = launcher_theme.log_theme_selection("Hell", logger)
    assert selected == "Hell"
    assert "Launcher-Theme gesetzt: Hell" in caplog.text
