from __future__ import annotations

from dataclasses import dataclass


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
}


def resolve_spacing_profile(name: str) -> SpacingProfile:
    return SPACING_PROFILES.get(name, SPACING_PROFILES["Standard"])


def resolve_interface_profile(
    name: str, large_controls: bool
) -> InterfaceProfile:
    base = INTERFACE_PROFILES.get(name, INTERFACE_PROFILES["Standard"])
    if not large_controls:
        return base
    return InterfaceProfile(
        control_height=base.control_height + 12,
        table_row_height=base.table_row_height + 12,
        compact_button_min_width=max(base.compact_button_min_width, 132),
        log_font_delta=2,
    )
