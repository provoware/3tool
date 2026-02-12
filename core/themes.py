from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Sequence, Tuple

FOCUS_STYLE = (
    "QWidget:focus{outline:2px solid #ffbf00;outline-offset:1px;} "
    "QLineEdit:focus,QComboBox:focus,QSpinBox:focus,"
    "QAbstractItemView:focus,QPushButton:focus,QTabBar::tab:focus{"
    "outline:2px solid #ffbf00;outline-offset:1px;}"
)

THEME_DEFINITIONS: Sequence[Tuple[str, str]] = (
    (
        "Modern",
        "QWidget{background-color:#f6f7fb;color:#1e1e1e;} "
        "QPushButton{background-color:#e6e8f0;color:#1e1e1e;border-radius:4px;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#ffffff;color:#1e1e1e;} "
        "QWidget:focus{outline:2px solid #1a73e8;}",
    ),
    (
        "Hell",
        "QWidget{background-color:#ffffff;color:#202020;} "
        "QPushButton{background-color:#e0e0e0;color:#202020;}" + FOCUS_STYLE,
    ),
    (
        "Dunkel",
        "QWidget{background-color:#2b2b2b;color:#e0e0e0;} "
        "QPushButton{background-color:#444;color:#e0e0e0;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#3a3a3a;color:#f0f0f0;} "
        "QWidget:focus{outline:2px solid #90caf9;}",
    ),
    (
        "Sepia",
        "QWidget{background-color:#f4ecd8;color:#5b4636;} "
        "QPushButton{background-color:#d6c3a0;color:#5b4636;}" + FOCUS_STYLE,
    ),
    (
        "Hochkontrast Hell",
        "QWidget{background-color:#ffffff;color:#000000;} "
        "QPushButton{background-color:#000000;color:#ffffff;border:2px solid #000000;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#ffffff;color:#000000;border:2px solid #000000;}"
        "QHeaderView::section{background-color:#000000;color:#ffffff;}"
        + FOCUS_STYLE,
    ),
    (
        "Hochkontrast Dunkel",
        "QWidget{background-color:#000000;color:#ffffff;} "
        "QPushButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#000000;color:#ffffff;border:2px solid #ffffff;}"
        "QHeaderView::section{background-color:#ffffff;color:#000000;}"
        + FOCUS_STYLE,
    ),
)


def load_themes(logger: Optional[logging.Logger] = None) -> Dict[str, str]:
    """Lädt die Theme-Definitionen und warnt bei doppelten Namen."""
    active_logger = logger or logging.getLogger(__name__)
    themes: Dict[str, str] = {}
    duplicates: List[str] = []
    for entry in THEME_DEFINITIONS:
        if not isinstance(entry, tuple) or len(entry) != 2:
            active_logger.warning(
                "Theme-Eintrag ist ungueltig: %r (erwartet (Name, CSS))", entry
            )
            continue
        name, css = entry
        if not isinstance(name, str) or not name.strip():
            active_logger.warning("Theme-Name ist ungueltig: %r", name)
            continue
        if not isinstance(css, str) or not css.strip():
            active_logger.warning("Theme-CSS ist leer fuer: %r", name)
            continue
        if name in themes:
            duplicates.append(name)
            continue
        themes[name] = css

    if duplicates:
        active_logger.warning(
            "Doppelte Theme-Namen gefunden: %s",
            ", ".join(sorted(set(duplicates))),
        )

    _warn_low_contrast(themes, active_logger)
    return themes


def _warn_low_contrast(themes: Dict[str, str], logger: logging.Logger) -> None:
    for name, css in themes.items():
        colors = _extract_widget_colors(css)
        if not colors:
            continue
        foreground, background = colors
        ratio = _contrast_ratio(foreground, background)
        if ratio is None:
            continue
        if ratio < 4.5:
            logger.warning(
                "Theme '%s' hat niedrigen Kontrast (%.2f:1) zwischen %s und %s.",
                name,
                ratio,
                foreground,
                background,
            )


def _extract_widget_colors(css: str) -> Optional[Tuple[str, str]]:
    if not isinstance(css, str):
        return None
    widget_match = re.search(r"QWidget\s*\{([^}]*)\}", css)
    if not widget_match:
        return None
    block = widget_match.group(1)
    background = _find_hex_color(block, "background-color")
    foreground = _find_hex_color(block, "color")
    if not background or not foreground:
        return None
    return foreground, background


def _find_hex_color(block: str, property_name: str) -> Optional[str]:
    match = re.search(
        rf"{re.escape(property_name)}\s*:\s*(#[0-9a-fA-F]{{3,6}})",
        block,
    )
    if not match:
        return None
    return match.group(1)


def _contrast_ratio(foreground: str, background: str) -> Optional[float]:
    fg_rgb = _hex_to_rgb(foreground)
    bg_rgb = _hex_to_rgb(background)
    if fg_rgb is None or bg_rgb is None:
        return None
    lum_fg = _relative_luminance(fg_rgb)
    lum_bg = _relative_luminance(bg_rgb)
    lighter = max(lum_fg, lum_bg)
    darker = min(lum_fg, lum_bg)
    return (lighter + 0.05) / (darker + 0.05)


def _hex_to_rgb(color: str) -> Optional[Tuple[int, int, int]]:
    if not isinstance(color, str):
        return None
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    if len(color) != 6:
        return None
    try:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    except ValueError:
        return None
    return r, g, b


def _relative_luminance(rgb: Tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        value = c / 255.0
        if value <= 0.03928:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
