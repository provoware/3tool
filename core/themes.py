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
    "QToolButton{min-height:32px;padding:6px 10px;font-weight:600;border-radius:8px;} "
    "QPushButton:disabled{opacity:0.75;} "
    "QToolButton:disabled{opacity:0.75;} "
    "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit,QTextBrowser{"
    "min-height:30px;padding:4px 8px;border-radius:6px;} "
    "QCheckBox,QRadioButton{spacing:8px;padding:2px 0;} "
    "QCheckBox::indicator,QRadioButton::indicator{width:20px;height:20px;} "
    "QComboBox::drop-down{width:30px;border:0;} "
    "QScrollBar:vertical{min-width:12px;} "
    "QScrollBar:horizontal{min-height:12px;} "
    "QGroupBox{font-weight:600;} "
    "QGroupBox::title{padding:0 6px;} "
    "QToolTip{border:1px solid #7a8699;padding:6px;} "
    "QHeaderView::section{padding:6px;font-weight:700;} "
    "QProgressBar{border-radius:6px;text-align:center;min-height:18px;} "
    "QProgressBar::chunk{border-radius:6px;} "
    "QFrame[dashboardCard='true']{border:1px solid #7a8699;border-radius:10px;padding:6px;} "
    "QLabel[metricLabel='true']{font-size:11px;font-weight:600;letter-spacing:0.3px;} "
    "QLabel[metricValue='true']{font-size:24px;font-weight:700;} "
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
        "QToolButton{background-color:#e6e8f0;color:#1e1e1e;border:1px solid #c9ced8;} "
        "QPushButton:hover{background-color:#dfe4ef;} "
        "QToolButton:hover{background-color:#dfe4ef;} "
        "QPushButton:pressed{background-color:#cfd6e4;} "
        "QToolButton:pressed{background-color:#cfd6e4;} "
        "QCheckBox::indicator,QRadioButton::indicator{border:2px solid #4b5563;background:#ffffff;} "
        "QCheckBox::indicator:checked,QRadioButton::indicator:checked{background:#1a73e8;border-color:#1a73e8;} "
        "QComboBox::drop-down{background:#e6e8f0;} "
        "QScrollBar::handle:vertical,QScrollBar::handle:horizontal{background:#9aa3b2;border-radius:6px;} "
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
        "Nachtblau Pro",
        "QWidget{background-color:#101827;color:#e6edf7;} "
        "QPushButton{background-color:#20324f;color:#e6edf7;border:1px solid #46618c;} "
        "QToolButton{background-color:#20324f;color:#e6edf7;border:1px solid #46618c;} "
        "QPushButton:hover{background-color:#284063;} "
        "QToolButton:hover{background-color:#284063;} "
        "QPushButton:pressed{background-color:#314b70;} "
        "QToolButton:pressed{background-color:#314b70;} "
        "QCheckBox::indicator,QRadioButton::indicator{border:2px solid #9ec4ff;background:#16243a;} "
        "QCheckBox::indicator:checked,QRadioButton::indicator:checked{background:#6ea7ff;border-color:#6ea7ff;} "
        "QComboBox::drop-down{background:#20324f;} "
        "QScrollBar::handle:vertical,QScrollBar::handle:horizontal{background:#6ea7ff;border-radius:6px;} "
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
        "Hochkontrast Hell",
        "QWidget{background-color:#ffffff;color:#000000;} "
        "QPushButton{background-color:#000000;color:#ffffff;border:2px solid #000000;}"
        "QToolButton{background-color:#000000;color:#ffffff;border:2px solid #000000;}"
        "QPushButton:hover,QToolButton:hover{background-color:#1f2937;}"
        "QPushButton:pressed,QToolButton:pressed{background-color:#374151;}"
        "QCheckBox::indicator,QRadioButton::indicator{border:2px solid #000000;background:#ffffff;}"
        "QCheckBox::indicator:checked,QRadioButton::indicator:checked{background:#000000;border-color:#000000;}"
        "QComboBox::drop-down{background:#000000;}"
        "QScrollBar::handle:vertical,QScrollBar::handle:horizontal{background:#000000;border-radius:6px;}"
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
        "Hochkontrast Dunkel",
        "QWidget{background-color:#000000;color:#ffffff;} "
        "QPushButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;}"
        "QToolButton{background-color:#ffffff;color:#000000;border:2px solid #ffffff;}"
        "QPushButton:hover{background-color:#f3f4f6;}"
        "QToolButton:hover{background-color:#f3f4f6;}"
        "QPushButton:pressed{background-color:#d1d5db;}"
        "QToolButton:pressed{background-color:#d1d5db;}"
        "QCheckBox::indicator,QRadioButton::indicator{border:2px solid #ffffff;background:#000000;}"
        "QCheckBox::indicator:checked,QRadioButton::indicator:checked{background:#ffffff;border-color:#ffffff;}"
        "QComboBox::drop-down{background:#ffffff;color:#000000;}"
        "QScrollBar::handle:vertical,QScrollBar::handle:horizontal{background:#ffffff;border-radius:6px;}"
        "QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{"
        "background-color:#000000;color:#ffffff;border:2px solid #ffffff;}"
        "QHeaderView::section{background-color:#ffffff;color:#000000;}"
        "QTableView::item:selected,QListView::item:selected{"
        "background-color:#ffffff;color:#000000;}"
        "QProgressBar{background-color:#000000;color:#ffffff;border:2px solid #ffffff;} "
        "QProgressBar::chunk{background-color:#ffffff;} "
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
        widget_colors = _extract_widget_colors(css)
        if not widget_colors:
            continue
        foreground, background = widget_colors
        ratio = _contrast_ratio(foreground, background)
        if ratio is not None and ratio < 7.0:
            logger.warning(
                "Theme '%s' hat niedrigen Grundkontrast (%.2f:1) zwischen %s und %s.",
                name,
                ratio,
                foreground,
                background,
            )

        input_colors = _extract_input_colors(css)
        if not input_colors:
            logger.warning(
                "Theme '%s' hat keine klaren Eingabefarben fuer Felder.",
                name,
            )
            continue
        input_foreground, input_background = input_colors
        input_ratio = _contrast_ratio(input_foreground, input_background)
        if input_ratio is not None and input_ratio < 7.0:
            logger.warning(
                "Theme '%s' hat niedrigen Feldkontrast (%.2f:1) zwischen %s und %s.",
                name,
                input_ratio,
                input_foreground,
                input_background,
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


def _extract_input_colors(css: str) -> Optional[Tuple[str, str]]:
    if not isinstance(css, str):
        return None
    field_match = re.search(r"QLineEdit[^\{]*\{([^}]*)\}", css)
    if not field_match:
        return None
    block = field_match.group(1)
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
        return float(((value + 0.055) / 1.055) ** 2.4)

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
