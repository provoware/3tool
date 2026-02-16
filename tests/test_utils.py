from datetime import datetime
from pathlib import Path

import pytest

from core.utils import build_out_name, mark_used_filename


def test_build_out_name_template_renders() -> None:
    now = datetime(2024, 1, 2, 3, 4, 5)
    out_dir = Path("/tmp/out")
    result = build_out_name(
        "musik.mp3",
        out_dir,
        template="{audio_name}_{video_laenge}_{qualitaet}_{abmasse}_{form}.mp4",
        now=now,
        duration_seconds=3723,
        quality="crf18_fast",
        resolution="1920x1080",
        form="slideshow",
    )
    assert result == out_dir / "musik_3723s_crf18_fast_1920x1080_slideshow.mp4"


def test_build_out_name_rejects_unknown_placeholder() -> None:
    with pytest.raises(ValueError):
        build_out_name(
            "musik.mp3", Path("/tmp/out"), template="{unbekannt}.mp4"
        )


def test_mark_used_filename_appends_suffix() -> None:
    result = mark_used_filename(Path("Urlaub Foto.PNG"))

    assert result == "urlaub_foto_benutzt.png"


def test_build_out_name_normalizes_spaces_and_repeated_underscores() -> None:
    out_dir = Path("/tmp/out")
    result = build_out_name(
        "musik.mp3",
        out_dir,
        template="  Mein   Export  __Final  ",
    )
    assert result == out_dir / "Mein_Export_Final.mp4"


def test_build_out_name_replaces_hidden_prefix_with_safe_default() -> None:
    out_dir = Path("/tmp/out")
    result = build_out_name("musik.mp3", out_dir, template=".env")
    assert result == out_dir / "output.env.mp4"


def test_build_out_name_limits_filename_length() -> None:
    out_dir = Path("/tmp/out")
    result = build_out_name("musik.mp3", out_dir, template="a" * 200)

    assert len(result.name) <= 124
