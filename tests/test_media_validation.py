from pathlib import Path

from core.media_validation import validate_media_pair


def test_validate_media_pair_valid(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    audio = tmp_path / "a.mp3"
    image.write_bytes(b"img")
    audio.write_bytes(b"aud")

    result = validate_media_pair(str(image), str(audio))
    assert result.valid is True


def test_validate_media_pair_rejects_missing_audio(tmp_path: Path) -> None:
    image = tmp_path / "a.jpg"
    image.write_bytes(b"img")

    result = validate_media_pair(str(image), "")
    assert result.valid is False
    assert "fehlt" in result.message
