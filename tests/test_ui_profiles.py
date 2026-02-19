from typing import Any, cast
from core.ui_profiles import (
    INTERFACE_PROFILES,
    SPACING_PROFILES,
    resolve_density_multiplier,
    resolve_interface_profile,
    resolve_spacing_profile,
)


def test_spacing_profile_fallback_to_standard() -> None:
    fallback = resolve_spacing_profile("Unbekannt")
    assert fallback == SPACING_PROFILES["Standard"]


def test_spacing_profile_supports_accessible_variant() -> None:
    accessible = resolve_spacing_profile("Barrierefrei")
    assert accessible.grid >= SPACING_PROFILES["Großzügig"].grid
    assert accessible.main >= SPACING_PROFILES["Großzügig"].main


def test_interface_profile_supports_profi_mode() -> None:
    profi = resolve_interface_profile("Profi", large_controls=False)
    assert profi == INTERFACE_PROFILES["Profi"]
    assert profi.compact_button_min_width >= 100


def test_interface_profile_large_controls_increase_sizes() -> None:
    base = resolve_interface_profile("Standard", large_controls=False)
    large = resolve_interface_profile("Standard", large_controls=True)
    assert large.control_height > base.control_height
    assert large.table_row_height > base.table_row_height
    assert large.log_font_delta >= 2


def test_interface_profile_supports_senior_mode() -> None:
    senior = resolve_interface_profile(
        "Seniorenfreundlich", large_controls=False
    )
    standard = resolve_interface_profile("Standard", large_controls=False)
    assert senior.control_height > standard.control_height
    assert senior.table_row_height > standard.table_row_height
    assert senior.compact_button_min_width >= 140
    assert senior.log_font_delta >= 2


def test_interface_profile_supports_max_accessible_mode() -> None:
    accessible = resolve_interface_profile(
        "Barrierefrei Max", large_controls=False
    )
    senior = resolve_interface_profile(
        "Seniorenfreundlich", large_controls=False
    )
    assert accessible.control_height > senior.control_height
    assert accessible.table_row_height > senior.table_row_height
    assert accessible.compact_button_min_width > senior.compact_button_min_width


def test_interface_profile_invalid_large_controls_falls_back() -> None:
    profile = resolve_interface_profile(
        "Standard", large_controls=cast(Any, "ja")
    )
    assert profile == INTERFACE_PROFILES["Standard"]


def test_density_profile_scales_with_font_and_dpi() -> None:
    compact = resolve_density_multiplier("Kompakt", font_size=13, dpi_scale=1.0)
    large = resolve_density_multiplier("Groß", font_size=20, dpi_scale=1.6)
    assert compact < 1.0
    assert large > compact


def test_density_profile_invalid_input_falls_back() -> None:
    fallback = resolve_density_multiplier("", font_size="x", dpi_scale="x")
    assert 0.85 <= fallback <= 1.9
