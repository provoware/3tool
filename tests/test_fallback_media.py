from pathlib import Path

from core.fallback_media import (
    dumps_audio_list,
    loads_audio_list,
    persist_fallback_media,
)


def test_audio_list_roundtrip() -> None:
    raw = dumps_audio_list(["/tmp/a.mp3", "/tmp/b.wav"])
    values = loads_audio_list(raw)
    assert values == ["/tmp/a.mp3", "/tmp/b.wav"]


def test_persist_fallback_media_copies_valid_files(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    image = src / "sample.png"
    audio1 = src / "a.mp3"
    audio2 = src / "b.wav"
    audio3 = src / "c.flac"
    for file in (image, audio1, audio2, audio3):
        file.write_bytes(b"demo")

    persisted_image, persisted_audio = persist_fallback_media(
        tmp_path / "target", str(image), [str(audio1), str(audio2), str(audio3)]
    )

    assert Path(persisted_image).exists()
    assert len(persisted_audio) == 2
    assert all(Path(item).exists() for item in persisted_audio)


def test_persist_fallback_media_ignores_invalid_files(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.txt"
    invalid.write_text("x", encoding="utf-8")
    image, audios = persist_fallback_media(
        tmp_path / "target", "", [str(invalid)]
    )
    assert image == ""
    assert audios == []
