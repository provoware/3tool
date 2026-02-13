from core.ui_profiles import (
    INTERFACE_PROFILES,
    SPACING_PROFILES,
    resolve_interface_profile,
    resolve_spacing_profile,
)


def test_spacing_profile_fallback_to_standard() -> None:
    fallback = resolve_spacing_profile("Unbekannt")
    assert fallback == SPACING_PROFILES["Standard"]


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
