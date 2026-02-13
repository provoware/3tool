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

BASE_COMPONENT_STYLE = (
    "QPushButton{min-height:32px;padding:6px 12px;font-weight:600;border-radius:8px;} "
    "QPushButton:disabled{opacity:0.75;} "
    "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit,QTextBrowser{"
    "min-height:30px;padding:4px 8px;border-radius:6px;} "
    "QGroupBox{font-weight:600;} "
    "QGroupBox::title{padding:0 6px;} "
    "QToolTip{border:1px solid #7a8699;padding:6px;} "
    "QHeaderView::section{padding:6px;font-weight:700;} "
    "QProgressBar{border-radius:6px;text-align:center;min-height:18px;} "
    "QProgressBar::chunk{border-radius:6px;} "
)

ACTIVE_SECTION_STYLE = (
    "QGroupBox{border:2px solid transparent;border-radius:8px;margin-top:10px;padding-top:8px;}"
    "QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px;}"
    "QGroupBox[activeSection='true']{border:3px solid #ffbf00;}"
)

THEME_DEFINITIONS: Sequence[Tuple[str, str]] = (
    (
        "Modern",
        "QWidget{background-color:#f6f7fb;color:#1e1e1e;} "
        "QPushButton{background-color:#e6e8f0;color:#1e1e1e;border:1px solid #c9ced8;} "
        "QPushButton:hover{background-color:#dfe4ef;} "
        "QPushButton:pressed{background-color:#cfd6e4;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#ffffff;color:#1e1e1e;border:1px solid #6b7280;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#c9dcff;color:#0f172a;} "
        "QProgressBar{background-color:#e7ebf3;color:#1e1e1e;border:1px solid #b7bfcc;} "
        "QProgressBar::chunk{background-color:#1a73e8;} "
        "QWidget:focus{outline:2px solid #1a73e8;}"
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Hell",
        "QWidget{background-color:#ffffff;color:#202020;} "
        "QPushButton{background-color:#e0e0e0;color:#202020;border:1px solid #b8b8b8;}"
        "QPushButton:hover{background-color:#d3d3d3;} "
        "QPushButton:pressed{background-color:#c4c4c4;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#f7f7f7;color:#111111;border:1px solid #5f6368;}"
        "QTableView::item:selected,QListView::item:selected{background-color:#dbeafe;color:#111111;} "
        "QProgressBar{background-color:#f1f1f1;color:#202020;border:1px solid #c3c3c3;} "
        "QProgressBar::chunk{background-color:#2f6ee4;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Dunkel",
        "QWidget{background-color:#2b2b2b;color:#e0e0e0;} "
        "QPushButton{background-color:#444;color:#e0e0e0;border:1px solid #5f6368;} "
        "QPushButton:hover{background-color:#505050;} "
        "QPushButton:pressed{background-color:#5a5a5a;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#3a3a3a;color:#f0f0f0;border:1px solid #9aa0a6;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#365d85;color:#ffffff;} "
        "QProgressBar{background-color:#3a3f46;color:#f0f0f0;border:1px solid #6e7781;} "
        "QProgressBar::chunk{background-color:#90caf9;} "
        "QWidget:focus{outline:2px solid #90caf9;}"
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Sepia",
        "QWidget{background-color:#f4ecd8;color:#5b4636;} "
        "QPushButton{background-color:#d6c3a0;color:#5b4636;border:1px solid #a78963;}"
        "QPushButton:hover{background-color:#ccb68f;} "
        "QPushButton:pressed{background-color:#bea87f;} "
        "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit{"
        "background-color:#fffaf0;color:#3e3024;border:1px solid #8b6f47;}"
        "QTableView::item:selected,QListView::item:selected{background-color:#ead8b8;color:#2f261e;} "
        "QProgressBar{background-color:#efe2c8;color:#3e3024;border:1px solid #b49569;} "
        "QProgressBar::chunk{background-color:#8b6f47;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Hochkontrast Hell",
        "QWidget{background-color:#ffffff;color:#000000;} "
        "QPushButton{background-color:#000000;color:#ffffff;border:2px solid #000000;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#ffffff;color:#000000;border:2px solid #000000;}"
        "QHeaderView::section{background-color:#000000;color:#ffffff;}"
        "QProgressBar{background-color:#ffffff;color:#000000;border:2px solid #000000;} "
        "QProgressBar::chunk{background-color:#000000;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Blau Kontrast",
        "QWidget{background-color:#0b1f33;color:#f4f8ff;} "
        "QPushButton{background-color:#f4f8ff;color:#0b1f33;border:2px solid #f4f8ff;border-radius:5px;} "
        "QPushButton:disabled{background-color:#9db2c7;color:#1b2a39;border-color:#9db2c7;} "
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#102942;color:#f4f8ff;border:2px solid #7fc8ff;} "
        "QHeaderView::section{background-color:#f4f8ff;color:#0b1f33;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#7fc8ff;color:#001425;}"
        "QProgressBar{background-color:#102942;color:#f4f8ff;border:2px solid #7fc8ff;} "
        "QProgressBar::chunk{background-color:#7fc8ff;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Gruen Kontrast",
        "QWidget{background-color:#102015;color:#effff2;} "
        "QPushButton{background-color:#effff2;color:#102015;border:2px solid #effff2;border-radius:5px;} "
        "QPushButton:disabled{background-color:#9fbba7;color:#1f2f24;border-color:#9fbba7;} "
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#173121;color:#effff2;border:2px solid #8bf0b2;} "
        "QHeaderView::section{background-color:#effff2;color:#102015;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#8bf0b2;color:#0d1d13;}"
        "QProgressBar{background-color:#173121;color:#effff2;border:2px solid #8bf0b2;} "
        "QProgressBar::chunk{background-color:#8bf0b2;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Hochkontrast Dunkel",
        "QWidget{background-color:#000000;color:#ffffff;} "
        "QPushButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#000000;color:#ffffff;border:2px solid #ffffff;}"
        "QHeaderView::section{background-color:#ffffff;color:#000000;}"
        "QProgressBar{background-color:#000000;color:#ffffff;border:2px solid #ffffff;} "
        "QProgressBar::chunk{background-color:#ffffff;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Nachtblau Pro",
        "QWidget{background-color:#101827;color:#e6edf7;} "
        "QPushButton{background-color:#20324f;color:#e6edf7;border:1px solid #46618c;} "
        "QPushButton:hover{background-color:#284063;} "
        "QPushButton:pressed{background-color:#314b70;} "
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#16243a;color:#f2f7ff;border:2px solid #6ea7ff;} "
        "QHeaderView::section{background-color:#1f3252;color:#f2f7ff;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#6ea7ff;color:#081223;} "
        "QProgressBar{background-color:#16243a;color:#f2f7ff;border:2px solid #6ea7ff;} "
        "QProgressBar::chunk{background-color:#6ea7ff;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
    ),
    (
        "Sand Kontrast Pro",
        "QWidget{background-color:#fffaf2;color:#1f140a;} "
        "QPushButton{background-color:#3b2f1f;color:#fffaf2;border:1px solid #3b2f1f;} "
        "QPushButton:hover{background-color:#2f2619;} "
        "QPushButton:pressed{background-color:#241d13;} "
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#ffffff;color:#1f140a;border:2px solid #60482f;} "
        "QHeaderView::section{background-color:#3b2f1f;color:#fffaf2;} "
        "QTableView::item:selected,QListView::item:selected{background-color:#c59a64;color:#120d06;} "
        "QProgressBar{background-color:#ffffff;color:#1f140a;border:2px solid #60482f;} "
        "QProgressBar::chunk{background-color:#3b2f1f;} "
        + FOCUS_STYLE
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE,
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
        rf"(?:^|[;\s]){re.escape(property_name)}\s*:\s*"
        rf"(#[0-9a-fA-F]{{3,6}})(?:;|$)",
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
