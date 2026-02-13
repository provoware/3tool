import core.themes as themes


def test_accessible_themes_available() -> None:
    loaded = themes.load_themes()
    assert "Blau Kontrast" in loaded
    assert "Gruen Kontrast" in loaded
    assert "Nachtblau Pro" in loaded
    assert "Sand Kontrast Pro" in loaded


def test_accessible_themes_have_good_widget_contrast() -> None:
    loaded = themes.load_themes()
    for name in (
        "Blau Kontrast",
        "Gruen Kontrast",
        "Nachtblau Pro",
        "Sand Kontrast Pro",
    ):
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
