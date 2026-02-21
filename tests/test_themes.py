import logging
from pathlib import Path

import pytest

import core.themes as themes


def test_theme_catalog_includes_accessible_profiles() -> None:
    loaded = themes.load_themes()
    assert list(loaded.keys()) == [
        "Modern",
        "Nachtblau Pro",
        "Hochkontrast Hell",
        "Hochkontrast Dunkel",
        "Solarisiert Barrierefrei",
    ]


def test_validate_theme_contrast_covers_required_sections() -> None:
    report = themes.validate_theme_contrast("Solarisiert Barrierefrei")
    assert sorted(report.keys()) == sorted(themes.CONTRAST_REQUIREMENTS.keys())
    for ratio, minimum_ratio, passed in report.values():
        assert ratio >= minimum_ratio
        assert passed


def test_validate_theme_contrast_rejects_invalid_theme_name() -> None:
    import pytest

    with pytest.raises(ValueError):
        themes.validate_theme_contrast("")
    with pytest.raises(ValueError):
        themes.validate_theme_contrast("Unbekannt")


def test_accessible_themes_have_good_widget_contrast() -> None:
    loaded = themes.load_themes()
    for name in loaded:
        colors = themes._extract_widget_colors(loaded[name])
        assert colors is not None
        ratio = themes._contrast_ratio(colors[0], colors[1])
        assert ratio is not None
        assert ratio >= 7.0


def test_themes_include_active_section_style() -> None:
    loaded = themes.load_themes()
    for name, css in loaded.items():
        assert "QGroupBox[activeSection='true']" in css, name


def test_input_fields_have_explicit_border() -> None:
    loaded = themes.load_themes()
    for name, css in loaded.items():
        assert "QLineEdit" in css, name
        assert "border:" in css, name


def test_accessible_themes_have_good_input_field_contrast() -> None:
    loaded = themes.load_themes()
    for name in loaded:
        colors = themes._extract_input_colors(loaded[name])
        assert colors is not None, name
        ratio = themes._contrast_ratio(colors[0], colors[1])
        assert ratio is not None
        assert ratio >= 7.0


def test_themes_style_settings_controls_consistently() -> None:
    loaded = themes.load_themes()
    for name, css in loaded.items():
        assert "QToolButton{" in css, name
        assert "QCheckBox::indicator" in css, name
        assert "QRadioButton::indicator" in css, name
        assert "QComboBox::drop-down" in css, name


def test_theme_tokens_have_required_schema() -> None:
    for name, token_map in themes.THEME_TOKENS.items():
        themes._validate_theme_tokens(token_map)
        for key in themes.TOKEN_KEYS:
            assert key in token_map, f"{name}: {key}"


def test_build_theme_css_uses_focus_token() -> None:
    css = themes._build_theme_css(themes.THEME_TOKENS["Modern"])
    assert "QWidget:focus" in css
    assert themes.THEME_TOKENS["Modern"]["focus_color"] in css


def test_build_theme_css_adds_focus_style_for_table_cells() -> None:
    css = themes._build_theme_css(themes.THEME_TOKENS["Modern"])
    assert "QTableView::item:focus" in css
    assert "QTreeView::item:focus" in css
    assert "QListView::item:focus" in css


def test_theme_includes_primary_action_button_states() -> None:
    for name, token_map in themes.THEME_TOKENS.items():
        css = themes._build_theme_css(token_map)
        assert "QPushButton[accentRole='primaryAction']{" in css, name
        assert ":hover" in css, name
        assert ":pressed" in css, name
        assert ":disabled" in css, name
        assert ":focus" in css, name
        assert "[readyPulse='a']" in css, name
        assert "[readyPulse='b']" in css, name


def test_base_component_style_uses_font_relative_units() -> None:
    css = themes.BASE_COMPONENT_STYLE
    assert "min-height:2.4em" in css
    assert "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit,QTextBrowser" in css
    assert "font-size:1.7em" in css


def test_choose_high_contrast_foreground_prefers_black_on_light_bg() -> None:
    selected = themes._choose_high_contrast_foreground("#fdf6e3", 7.0)
    assert selected == "#000000"


def test_choose_high_contrast_foreground_prefers_white_on_dark_bg() -> None:
    selected = themes._choose_high_contrast_foreground("#101827", 7.0)
    assert selected == "#ffffff"


def test_ensure_accessible_theme_tokens_fixes_low_contrast(
    caplog: pytest.LogCaptureFixture,
) -> None:
    weak = dict(themes.THEME_TOKENS["Modern"])
    weak["button_bg"] = "#ffffff"
    weak["button_fg"] = "#f8f8f8"

    caplog.set_level(logging.WARNING)
    fixed = themes.ensure_accessible_theme_tokens("Test", weak)

    ratio = themes._contrast_ratio(fixed["button_fg"], fixed["button_bg"])
    assert ratio is not None
    assert ratio >= themes.CONTRAST_REQUIREMENTS["button"][2]
    assert "Kontrast fuer 'button' war zu niedrig" in caplog.text


def test_gui_primary_action_has_no_hardcoded_button_colors() -> None:
    gui_source = Path("videobatch_gui.py").read_text(encoding="utf-8").lower()
    forbidden = ["#005bbb", "#1e8e3e", "#27ae60", "color:white"]
    for value in forbidden:
        assert value not in gui_source


def test_theme_css_has_border_based_focus_strategy_for_keyboard_navigation() -> (
    None
):
    for name, token_map in themes.THEME_TOKENS.items():
        css = themes._build_theme_css(token_map)
        assert "QPushButton:focus" in css, name
        assert "QLineEdit:focus" in css, name
        assert "QCheckBox:focus" in css, name
        assert "border:2px solid" in css, name
