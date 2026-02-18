from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Sequence, Tuple

BASE_COMPONENT_STYLE = (
    "QPushButton{min-height:2.4em;padding:0.42em 0.86em;font-weight:600;border-radius:0.58em;} "
    "QToolButton{min-height:2.4em;padding:0.42em 0.72em;font-weight:600;border-radius:0.58em;} "
    "QPushButton:disabled{opacity:0.82;} "
    "QToolButton:disabled{opacity:0.82;} "
    "QLineEdit,QSpinBox,QComboBox,QPlainTextEdit,QTextBrowser{"
    "min-height:2.2em;padding:0.28em 0.58em;border-radius:0.42em;} "
    "QCheckBox,QRadioButton{spacing:8px;padding:2px 0;} "
    "QCheckBox::indicator,QRadioButton::indicator{width:1.4em;height:1.4em;} "
    "QComboBox::drop-down{width:2.2em;border:0;} "
    "QScrollBar:vertical{min-width:0.9em;} "
    "QScrollBar:horizontal{min-height:0.9em;} "
    "QGroupBox{font-weight:600;} "
    "QGroupBox::title{padding:0 6px;} "
    "QToolTip{border:1px solid #7a8699;padding:6px;} "
    "QHeaderView::section{padding:6px;font-weight:700;} "
    "QProgressBar{border-radius:0.42em;text-align:center;min-height:1.35em;} "
    "QProgressBar::chunk{border-radius:0.42em;} "
    "QFrame[dashboardCard='true']{border:1px solid #7a8699;border-radius:0.72em;padding:0.42em;} "
    "QLabel[metricLabel='true']{font-size:0.88em;font-weight:600;letter-spacing:0.02em;} "
    "QLabel[metricValue='true']{font-size:1.7em;font-weight:700;} "
    "QFrame[actionTile='true']{border:1px solid #7a8699;border-radius:0.72em;} "
    "QLabel[actionTileDetail='true']{font-size:0.95em;line-height:1.25;} "
    "QWidget[responsive='compact'] QPushButton,QWidget[responsive='compact'] QToolButton{min-height:2.1em;padding:0.3em 0.58em;} "
    "QWidget[responsive='expanded'] QPushButton,QWidget[responsive='expanded'] QToolButton{min-height:2.8em;padding:0.58em 1em;} "
)

ACTIVE_SECTION_STYLE = (
    "QGroupBox{border:2px solid transparent;border-radius:8px;margin-top:10px;padding-top:8px;}"
    "QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 4px;}"
    "QGroupBox[activeSection='true']{border:3px solid #ffbf00;}"
)

TOKEN_KEYS: Tuple[str, ...] = (
    "widget_bg",
    "widget_fg",
    "button_bg",
    "button_fg",
    "button_border",
    "button_hover",
    "button_pressed",
    "indicator_border",
    "indicator_bg",
    "indicator_checked",
    "dropdown_bg",
    "scroll_handle",
    "field_bg",
    "field_fg",
    "field_border",
    "header_bg",
    "header_fg",
    "selection_bg",
    "selection_fg",
    "progress_bg",
    "progress_fg",
    "progress_border",
    "progress_chunk",
    "focus_color",
    "action_primary_bg",
    "action_primary_fg",
    "action_primary_border",
    "action_primary_hover",
    "action_primary_pressed",
    "action_primary_disabled_bg",
    "action_primary_disabled_fg",
    "action_primary_focus",
    "action_ready_bg_a",
    "action_ready_bg_b",
    "preview_info_bg",
    "preview_info_border",
    "preview_info_fg",
    "preview_success_bg",
    "preview_success_border",
    "preview_success_fg",
    "preview_danger_bg",
    "preview_danger_border",
    "preview_danger_fg",
)

THEME_TOKENS: Dict[str, Dict[str, str]] = {
    "Modern": {
        "widget_bg": "#f6f7fb",
        "widget_fg": "#1e1e1e",
        "button_bg": "#e6e8f0",
        "button_fg": "#1e1e1e",
        "button_border": "#c9ced8",
        "button_hover": "#dfe4ef",
        "button_pressed": "#cfd6e4",
        "indicator_border": "#4b5563",
        "indicator_bg": "#ffffff",
        "indicator_checked": "#1a73e8",
        "dropdown_bg": "#e6e8f0",
        "scroll_handle": "#9aa3b2",
        "field_bg": "#ffffff",
        "field_fg": "#1e1e1e",
        "field_border": "#6b7280",
        "header_bg": "#f6f7fb",
        "header_fg": "#1e1e1e",
        "selection_bg": "#c9dcff",
        "selection_fg": "#0f172a",
        "progress_bg": "#e7ebf3",
        "progress_fg": "#1e1e1e",
        "progress_border": "#b7bfcc",
        "progress_chunk": "#1a73e8",
        "focus_color": "#1a73e8",
        "action_primary_bg": "#005bbb",
        "action_primary_fg": "#ffffff",
        "action_primary_border": "#004a96",
        "action_primary_hover": "#0a6ed1",
        "action_primary_pressed": "#004a96",
        "action_primary_disabled_bg": "#7f9ec2",
        "action_primary_disabled_fg": "#e9f1ff",
        "action_primary_focus": "#ffbf00",
        "action_ready_bg_a": "#1e8e3e",
        "action_ready_bg_b": "#27ae60",
        "preview_info_bg": "#e8f0fe",
        "preview_info_border": "#1a73e8",
        "preview_info_fg": "#1a73e8",
        "preview_success_bg": "#e6f4ea",
        "preview_success_border": "#137333",
        "preview_success_fg": "#137333",
        "preview_danger_bg": "#fce8e6",
        "preview_danger_border": "#c5221f",
        "preview_danger_fg": "#c5221f",
    },
    "Nachtblau Pro": {
        "widget_bg": "#101827",
        "widget_fg": "#e6edf7",
        "button_bg": "#20324f",
        "button_fg": "#e6edf7",
        "button_border": "#46618c",
        "button_hover": "#284063",
        "button_pressed": "#314b70",
        "indicator_border": "#9ec4ff",
        "indicator_bg": "#16243a",
        "indicator_checked": "#6ea7ff",
        "dropdown_bg": "#20324f",
        "scroll_handle": "#6ea7ff",
        "field_bg": "#16243a",
        "field_fg": "#f2f7ff",
        "field_border": "#6ea7ff",
        "header_bg": "#1f3252",
        "header_fg": "#f2f7ff",
        "selection_bg": "#6ea7ff",
        "selection_fg": "#081223",
        "progress_bg": "#16243a",
        "progress_fg": "#f2f7ff",
        "progress_border": "#6ea7ff",
        "progress_chunk": "#6ea7ff",
        "focus_color": "#ffbf00",
        "action_primary_bg": "#6ea7ff",
        "action_primary_fg": "#081223",
        "action_primary_border": "#9ec4ff",
        "action_primary_hover": "#8fb9ff",
        "action_primary_pressed": "#5d97e8",
        "action_primary_disabled_bg": "#344865",
        "action_primary_disabled_fg": "#b9cae3",
        "action_primary_focus": "#ffbf00",
        "action_ready_bg_a": "#38a169",
        "action_ready_bg_b": "#48bb78",
        "preview_info_bg": "#1f3252",
        "preview_info_border": "#6ea7ff",
        "preview_info_fg": "#9ec4ff",
        "preview_success_bg": "#173a2a",
        "preview_success_border": "#48bb78",
        "preview_success_fg": "#9ae6b4",
        "preview_danger_bg": "#4a1f28",
        "preview_danger_border": "#fc8181",
        "preview_danger_fg": "#feb2b2",
    },
    "Hochkontrast Hell": {
        "widget_bg": "#ffffff",
        "widget_fg": "#000000",
        "button_bg": "#000000",
        "button_fg": "#ffffff",
        "button_border": "#000000",
        "button_hover": "#1f2937",
        "button_pressed": "#374151",
        "indicator_border": "#000000",
        "indicator_bg": "#ffffff",
        "indicator_checked": "#000000",
        "dropdown_bg": "#000000",
        "scroll_handle": "#000000",
        "field_bg": "#ffffff",
        "field_fg": "#000000",
        "field_border": "#000000",
        "header_bg": "#000000",
        "header_fg": "#ffffff",
        "selection_bg": "#000000",
        "selection_fg": "#ffffff",
        "progress_bg": "#ffffff",
        "progress_fg": "#000000",
        "progress_border": "#000000",
        "progress_chunk": "#000000",
        "focus_color": "#ffbf00",
        "action_primary_bg": "#000000",
        "action_primary_fg": "#ffffff",
        "action_primary_border": "#000000",
        "action_primary_hover": "#1f2937",
        "action_primary_pressed": "#111827",
        "action_primary_disabled_bg": "#4b5563",
        "action_primary_disabled_fg": "#f9fafb",
        "action_primary_focus": "#ffbf00",
        "action_ready_bg_a": "#000000",
        "action_ready_bg_b": "#1f2937",
        "preview_info_bg": "#ffffff",
        "preview_info_border": "#000000",
        "preview_info_fg": "#000000",
        "preview_success_bg": "#ffffff",
        "preview_success_border": "#000000",
        "preview_success_fg": "#000000",
        "preview_danger_bg": "#ffffff",
        "preview_danger_border": "#000000",
        "preview_danger_fg": "#000000",
    },
    "Hochkontrast Dunkel": {
        "widget_bg": "#000000",
        "widget_fg": "#ffffff",
        "button_bg": "#ffffff",
        "button_fg": "#000000",
        "button_border": "#ffffff",
        "button_hover": "#e5e7eb",
        "button_pressed": "#cbd5e1",
        "indicator_border": "#ffffff",
        "indicator_bg": "#000000",
        "indicator_checked": "#ffffff",
        "dropdown_bg": "#ffffff",
        "scroll_handle": "#ffffff",
        "field_bg": "#000000",
        "field_fg": "#ffffff",
        "field_border": "#ffffff",
        "header_bg": "#ffffff",
        "header_fg": "#000000",
        "selection_bg": "#ffffff",
        "selection_fg": "#000000",
        "progress_bg": "#000000",
        "progress_fg": "#ffffff",
        "progress_border": "#ffffff",
        "progress_chunk": "#ffffff",
        "focus_color": "#ffbf00",
        "action_primary_bg": "#ffffff",
        "action_primary_fg": "#000000",
        "action_primary_border": "#ffffff",
        "action_primary_hover": "#e5e7eb",
        "action_primary_pressed": "#cbd5e1",
        "action_primary_disabled_bg": "#6b7280",
        "action_primary_disabled_fg": "#ffffff",
        "action_primary_focus": "#ffbf00",
        "action_ready_bg_a": "#ffffff",
        "action_ready_bg_b": "#e5e7eb",
        "preview_info_bg": "#000000",
        "preview_info_border": "#ffffff",
        "preview_info_fg": "#ffffff",
        "preview_success_bg": "#000000",
        "preview_success_border": "#ffffff",
        "preview_success_fg": "#ffffff",
        "preview_danger_bg": "#000000",
        "preview_danger_border": "#ffffff",
        "preview_danger_fg": "#ffffff",
    },
    "Solarisiert Barrierefrei": {
        "widget_bg": "#fdf6e3",
        "widget_fg": "#073642",
        "button_bg": "#073642",
        "button_fg": "#fdf6e3",
        "button_border": "#002b36",
        "button_hover": "#0b4f62",
        "button_pressed": "#002b36",
        "indicator_border": "#073642",
        "indicator_bg": "#fdf6e3",
        "indicator_checked": "#005f87",
        "dropdown_bg": "#073642",
        "scroll_handle": "#586e75",
        "field_bg": "#ffffff",
        "field_fg": "#073642",
        "field_border": "#073642",
        "header_bg": "#073642",
        "header_fg": "#fdf6e3",
        "selection_bg": "#005f87",
        "selection_fg": "#fdf6e3",
        "progress_bg": "#eee8d5",
        "progress_fg": "#073642",
        "progress_border": "#073642",
        "progress_chunk": "#005f87",
        "focus_color": "#b58900",
        "action_primary_bg": "#005f87",
        "action_primary_fg": "#fdf6e3",
        "action_primary_border": "#004f70",
        "action_primary_hover": "#0a739f",
        "action_primary_pressed": "#004f70",
        "action_primary_disabled_bg": "#839496",
        "action_primary_disabled_fg": "#fdf6e3",
        "action_primary_focus": "#b58900",
        "action_ready_bg_a": "#0d6f42",
        "action_ready_bg_b": "#14844f",
        "preview_info_bg": "#eaf5ff",
        "preview_info_border": "#005f87",
        "preview_info_fg": "#004f70",
        "preview_success_bg": "#e8f7ef",
        "preview_success_border": "#0d6f42",
        "preview_success_fg": "#0d6f42",
        "preview_danger_bg": "#fff1eb",
        "preview_danger_border": "#9c2f00",
        "preview_danger_fg": "#9c2f00",
    },
}

CONTRAST_REQUIREMENTS: Dict[str, Tuple[str, str, float]] = {
    "widget": ("widget_fg", "widget_bg", 7.0),
    "field": ("field_fg", "field_bg", 7.0),
    "button": ("button_fg", "button_bg", 4.5),
    "selection": ("selection_fg", "selection_bg", 4.5),
    "primary_action": ("action_primary_fg", "action_primary_bg", 4.5),
}


def _validate_theme_tokens(tokens: Dict[str, str]) -> None:
    if not isinstance(tokens, dict):
        raise TypeError("Theme-Tokens muessen als dict uebergeben werden.")
    missing = [key for key in TOKEN_KEYS if key not in tokens]
    if missing:
        raise ValueError(f"Fehlende Theme-Tokens: {', '.join(missing)}")
    for key in TOKEN_KEYS:
        value = tokens[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Theme-Token '{key}' ist ungueltig.")


def _build_theme_css(tokens: Dict[str, str]) -> str:
    _validate_theme_tokens(tokens)
    return (
        f"QWidget{{background-color:{tokens['widget_bg']};color:{tokens['widget_fg']};}} "
        f"QPushButton{{background-color:{tokens['button_bg']};color:{tokens['button_fg']};border:2px solid {tokens['button_border']};}} "
        f"QToolButton{{background-color:{tokens['button_bg']};color:{tokens['button_fg']};border:2px solid {tokens['button_border']};}} "
        f"QPushButton:hover,QToolButton:hover{{background-color:{tokens['button_hover']};}} "
        f"QPushButton:pressed,QToolButton:pressed{{background-color:{tokens['button_pressed']};}} "
        f"QCheckBox::indicator,QRadioButton::indicator{{border:2px solid {tokens['indicator_border']};background:{tokens['indicator_bg']};}} "
        f"QCheckBox::indicator:checked,QRadioButton::indicator:checked{{background:{tokens['indicator_checked']};border-color:{tokens['indicator_checked']};}} "
        f"QComboBox::drop-down{{background:{tokens['dropdown_bg']};}} "
        f"QScrollBar::handle:vertical,QScrollBar::handle:horizontal{{background:{tokens['scroll_handle']};border-radius:6px;}} "
        f"QLineEdit,QComboBox,QSpinBox,QPlainTextEdit,QTextBrowser{{background-color:{tokens['field_bg']};color:{tokens['field_fg']};border:2px solid {tokens['field_border']};}} "
        f"QHeaderView::section{{background-color:{tokens['header_bg']};color:{tokens['header_fg']};}} "
        f"QTableView::item:selected,QListView::item:selected{{background-color:{tokens['selection_bg']};color:{tokens['selection_fg']};}} "
        f"QTableView::item:focus,QTreeView::item:focus,QListView::item:focus{{outline:2px solid {tokens['focus_color']};outline-offset:-1px;border:1px solid {tokens['focus_color']};}} "
        f"QProgressBar{{background-color:{tokens['progress_bg']};color:{tokens['progress_fg']};border:2px solid {tokens['progress_border']};}} "
        f"QProgressBar::chunk{{background-color:{tokens['progress_chunk']};}} "
        f"QWidget:focus{{outline:2px solid {tokens['focus_color']};outline-offset:1px;}}"
        f"QPushButton[accentRole='primaryAction']{{"
        f"background-color:{tokens['action_primary_bg']};"
        f"color:{tokens['action_primary_fg']};"
        f"border:2px solid {tokens['action_primary_border']};"
        "font-size:14pt;font-weight:bold;padding:4px 10px;"
        "}} "
        f"QPushButton[accentRole='primaryAction']:hover{{background-color:{tokens['action_primary_hover']};}} "
        f"QPushButton[accentRole='primaryAction']:pressed{{background-color:{tokens['action_primary_pressed']};}} "
        f"QPushButton[accentRole='primaryAction']:disabled{{"
        f"background-color:{tokens['action_primary_disabled_bg']};"
        f"color:{tokens['action_primary_disabled_fg']};"
        f"border-color:{tokens['action_primary_disabled_bg']};"
        "}} "
        f"QPushButton[accentRole='primaryAction']:focus{{outline:2px solid {tokens['action_primary_focus']};outline-offset:1px;}} "
        f"QPushButton[accentRole='primaryAction'][readyPulse='a']{{background-color:{tokens['action_ready_bg_a']};}} "
        f"QPushButton[accentRole='primaryAction'][readyPulse='b']{{background-color:{tokens['action_ready_bg_b']};}}"
        + BASE_COMPONENT_STYLE
        + ACTIVE_SECTION_STYLE
    )


THEME_DEFINITIONS: Sequence[Tuple[str, str]] = tuple(
    (name, _build_theme_css(tokens)) for name, tokens in THEME_TOKENS.items()
)

FALLBACK_FOREGROUND_CANDIDATES: Tuple[str, str] = ("#000000", "#ffffff")


def load_themes(logger: Optional[logging.Logger] = None) -> Dict[str, str]:
    """Lädt Theme-Definitionen, behebt schwachen Kontrast und warnt bei Duplikaten."""
    active_logger = logger or logging.getLogger(__name__)
    themes: Dict[str, str] = {}
    duplicates: List[str] = []
    for name, raw_tokens in THEME_TOKENS.items():
        if not isinstance(name, str) or not name.strip():
            active_logger.warning("Theme-Name ist ungueltig: %r", name)
            continue
        if not isinstance(raw_tokens, dict):
            active_logger.warning("Theme-Tokenmap ist ungueltig fuer: %r", name)
            continue
        if name in themes:
            duplicates.append(name)
            continue
        normalized_tokens = ensure_accessible_theme_tokens(
            name, raw_tokens, active_logger
        )
        css = _build_theme_css(normalized_tokens)
        themes[name] = css

    if duplicates:
        active_logger.warning(
            "Doppelte Theme-Namen gefunden: %s",
            ", ".join(sorted(set(duplicates))),
        )

    _warn_low_contrast(active_logger)
    return themes


def ensure_accessible_theme_tokens(
    theme_name: str,
    tokens: Dict[str, str],
    logger: Optional[logging.Logger] = None,
) -> Dict[str, str]:
    """Erzwingt Mindestkontrast und ersetzt schwache Schriftfarben automatisch."""
    if not isinstance(theme_name, str) or not theme_name.strip():
        raise ValueError("theme_name muss ein nicht-leerer String sein")
    _validate_theme_tokens(tokens)
    active_logger = logger or logging.getLogger(__name__)
    adjusted_tokens = dict(tokens)
    for section, (
        fg_key,
        bg_key,
        minimum_ratio,
    ) in CONTRAST_REQUIREMENTS.items():
        current_ratio = _contrast_ratio(
            adjusted_tokens[fg_key], adjusted_tokens[bg_key]
        )
        if current_ratio is None:
            raise ValueError(
                f"Theme '{theme_name}' hat ungueltige Farbe fuer '{section}'."
            )
        if current_ratio >= minimum_ratio:
            continue
        replacement = _choose_high_contrast_foreground(
            adjusted_tokens[bg_key], minimum_ratio
        )
        if replacement is None:
            active_logger.warning(
                "Theme '%s': Kontrast fuer '%s' bleibt niedrig (%.2f:1). "
                "Bitte Farben pruefen.",
                theme_name,
                section,
                current_ratio,
            )
            continue
        old_color = adjusted_tokens[fg_key]
        adjusted_tokens[fg_key] = replacement
        fixed_ratio = _contrast_ratio(replacement, adjusted_tokens[bg_key])
        if fixed_ratio is None:
            raise ValueError(
                f"Theme '{theme_name}' konnte nicht fuer '{section}' normalisiert werden."
            )
        active_logger.warning(
            "Theme '%s': Kontrast fuer '%s' war zu niedrig (%.2f:1). "
            "Textfarbe wurde von %s auf %s gesetzt (neu %.2f:1).",
            theme_name,
            section,
            current_ratio,
            old_color,
            replacement,
            fixed_ratio,
        )
    return adjusted_tokens


def _choose_high_contrast_foreground(
    background: str, minimum_ratio: float
) -> Optional[str]:
    if not isinstance(background, str) or not background.strip():
        return None
    if not isinstance(minimum_ratio, float) and not isinstance(
        minimum_ratio, int
    ):
        return None
    best_candidate: Optional[Tuple[str, float]] = None
    for candidate in FALLBACK_FOREGROUND_CANDIDATES:
        ratio = _contrast_ratio(candidate, background)
        if ratio is None:
            continue
        if best_candidate is None or ratio > best_candidate[1]:
            best_candidate = (candidate, ratio)
    if best_candidate is None:
        return None
    if best_candidate[1] < float(minimum_ratio):
        return None
    return best_candidate[0]


def get_theme_tokens(name: str) -> Dict[str, str]:
    if not isinstance(name, str) or name not in THEME_TOKENS:
        return dict(THEME_TOKENS["Modern"])
    return dict(THEME_TOKENS[name])


def _warn_low_contrast(logger: logging.Logger) -> None:
    for name in THEME_TOKENS:
        report = validate_theme_contrast(name)
        for section, (ratio, minimum_ratio, passed) in report.items():
            if not passed:
                logger.warning(
                    "Theme '%s' hat niedrigen %s-Kontrast (%.2f:1, erwartet >= %.2f:1).",
                    name,
                    section,
                    ratio,
                    minimum_ratio,
                )


def validate_theme_contrast(
    theme_name: str,
) -> Dict[str, Tuple[float, float, bool]]:
    """Validate required contrast pairs for a theme.

    Returns mapping section -> (ratio, minimum_ratio, passed).
    """
    if not isinstance(theme_name, str) or not theme_name.strip():
        raise ValueError("theme_name muss ein nicht-leerer String sein")
    if theme_name not in THEME_TOKENS:
        raise ValueError(f"Unbekanntes Theme: {theme_name}")
    tokens = THEME_TOKENS[theme_name]
    report: Dict[str, Tuple[float, float, bool]] = {}
    for section, (
        fg_key,
        bg_key,
        minimum_ratio,
    ) in CONTRAST_REQUIREMENTS.items():
        ratio = _contrast_ratio(tokens[fg_key], tokens[bg_key])
        if ratio is None:
            raise ValueError(
                f"Theme '{theme_name}' hat ungueltige Farbe fuer '{section}'."
            )
        report[section] = (ratio, minimum_ratio, ratio >= minimum_ratio)
    return report


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
