import core.themes as themes


def test_theme_catalog_is_limited_to_four_profiles() -> None:
    loaded = themes.load_themes()
    assert list(loaded.keys()) == [
        "Modern",
        "Nachtblau Pro",
        "Hochkontrast Hell",
        "Hochkontrast Dunkel",
    ]


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
