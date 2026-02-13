from __future__ import annotations

import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SpacingProfile:
    grid: int
    margins: int
    main: int


@dataclass(frozen=True)
class InterfaceProfile:
    control_height: int
    table_row_height: int
    compact_button_min_width: int
    log_font_delta: int


SPACING_PROFILES = {
    "Kompakt": SpacingProfile(grid=2, margins=2, main=4),
    "Standard": SpacingProfile(grid=4, margins=4, main=6),
    "Großzügig": SpacingProfile(grid=8, margins=8, main=10),
    "Barrierefrei": SpacingProfile(grid=12, margins=12, main=14),
}

INTERFACE_PROFILES = {
    "Standard": InterfaceProfile(
        control_height=28,
        table_row_height=24,
        compact_button_min_width=0,
        log_font_delta=0,
    ),
    "Profi": InterfaceProfile(
        control_height=32,
        table_row_height=28,
        compact_button_min_width=116,
        log_font_delta=0,
    ),
    "Seniorenfreundlich": InterfaceProfile(
        control_height=40,
        table_row_height=36,
        compact_button_min_width=140,
        log_font_delta=2,
    ),
    "Barrierefrei Max": InterfaceProfile(
        control_height=46,
        table_row_height=42,
        compact_button_min_width=168,
        log_font_delta=3,
    ),
}


def resolve_spacing_profile(name: str) -> SpacingProfile:
    if not isinstance(name, str) or not name.strip():
        LOGGER.warning(
            "Ungueltiges Abstandsprofil %r erhalten, nutze Standard.", name
        )
        name = "Standard"
    profile = SPACING_PROFILES.get(name, SPACING_PROFILES["Standard"])
    LOGGER.info(
        "Abstandsprofil aktiv: %s (grid=%s, margins=%s, main=%s)",
        name if name in SPACING_PROFILES else "Standard",
        profile.grid,
        profile.margins,
        profile.main,
    )
    return profile


def resolve_interface_profile(
    name: str, large_controls: bool
) -> InterfaceProfile:
    if not isinstance(name, str) or not name.strip():
        LOGGER.warning(
            "Ungueltiges Interface-Profil %r erhalten, nutze Standard.",
            name,
        )
        name = "Standard"
    if not isinstance(large_controls, bool):
        LOGGER.warning(
            "Ungueltiger large_controls-Wert %r erhalten, nutze False.",
            large_controls,
        )
        large_controls = False

    base = INTERFACE_PROFILES.get(name, INTERFACE_PROFILES["Standard"])
    if not large_controls:
        LOGGER.info(
            "Interface-Profil aktiv: %s (normal, control_height=%s)",
            name if name in INTERFACE_PROFILES else "Standard",
            base.control_height,
        )
        return base
    resolved = InterfaceProfile(
        control_height=base.control_height + 12,
        table_row_height=base.table_row_height + 12,
        compact_button_min_width=max(base.compact_button_min_width, 132),
        log_font_delta=2,
    )
    LOGGER.info(
        "Interface-Profil aktiv: %s (grosse Bedienelemente, control_height=%s)",
        name if name in INTERFACE_PROFILES else "Standard",
        resolved.control_height,
    )
    return resolved
