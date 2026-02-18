from datetime import datetime
from pathlib import Path

import pytest

from core.output_management import (
    build_dated_output_dir,
    classify_output_category,
    transfer_with_validation,
)


def test_classify_output_category_maps_audio_to_musik() -> None:
    assert classify_output_category("Video + Audio") == "musik"
    assert classify_output_category("Mehrere Audios, 1 Bild") == "musik"


def test_build_dated_output_dir_uses_date_and_category(tmp_path: Path) -> None:
    out_dir = build_dated_output_dir(
        tmp_path,
        "Slideshow",
        now=datetime(2026, 2, 3, 4, 5, 6),
    )
    assert out_dir == tmp_path / "2026-02-03" / "tracks"
    assert out_dir.exists()


def test_transfer_with_validation_copy_only(tmp_path: Path) -> None:
    src = tmp_path / "song.mp3"
    src.write_bytes(b"abc123")

    result = transfer_with_validation(
        src,
        tmp_path / "used",
        copy_only=True,
        suffix_label="benutzt",
    )

    assert result.validated is True
    assert result.target.exists()
    assert src.exists()


def test_transfer_with_validation_move(tmp_path: Path) -> None:
    src = tmp_path / "img.png"
    src.write_bytes(b"xyz")

    result = transfer_with_validation(
        src,
        tmp_path / "used",
        copy_only=False,
        suffix_label="benutzt",
    )

    assert result.validated is True
    assert result.target.exists()
    assert not src.exists()


def test_transfer_with_validation_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        transfer_with_validation(
            tmp_path / "missing.mp3",
            tmp_path / "used",
            copy_only=True,
            suffix_label="benutzt",
        )
