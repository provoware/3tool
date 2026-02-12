import core.themes as themes


def test_accessible_themes_available() -> None:
    loaded = themes.load_themes()
    assert "Blau Kontrast" in loaded
    assert "Gruen Kontrast" in loaded


def test_accessible_themes_have_good_widget_contrast() -> None:
    loaded = themes.load_themes()
    for name in ("Blau Kontrast", "Gruen Kontrast"):
        colors = themes._extract_widget_colors(loaded[name])
        assert colors is not None
        ratio = themes._contrast_ratio(colors[0], colors[1])
        assert ratio is not None
        assert ratio >= 7.0
