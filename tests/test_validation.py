from core.validation import (
    DEFAULT_AUDIO_BITRATE,
    DEFAULT_OUTPUT_TEMPLATE,
    normalize_audio_bitrate,
    validate_output_template,
)


def test_normalize_audio_bitrate_accepts_plain_number():
    result = normalize_audio_bitrate("256")

    assert result.is_valid is True
    assert result.value == "256k"
    assert "ergänzt" in result.message


def test_normalize_audio_bitrate_accepts_text_unit():
    result = normalize_audio_bitrate("1.5 mbit/s")

    assert result.is_valid is True
    assert result.value == "2M"


def test_normalize_audio_bitrate_rejects_invalid_input():
    result = normalize_audio_bitrate("abc")

    assert result.is_valid is False
    assert result.value == DEFAULT_AUDIO_BITRATE
    assert "Audiobitrate" in result.message


def test_validate_output_template_returns_default_for_invalid():
    result = validate_output_template("{unknown}.mp4")

    assert result.is_valid is False
    assert result.value == DEFAULT_OUTPUT_TEMPLATE
    assert "Erlaubt sind" in result.message
