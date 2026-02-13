import core.themes as themes


def test_theme_catalog_is_limited_to_three_profiles() -> None:
    loaded = themes.load_themes()
    assert list(loaded.keys()) == [
        "Modern",
        "Nachtblau Pro",
        "Hochkontrast Hell",
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
