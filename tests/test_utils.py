from datetime import datetime
from pathlib import Path

import pytest

from core.utils import build_out_name


def test_build_out_name_template_renders() -> None:
    now = datetime(2024, 1, 2, 3, 4, 5)
    out_dir = Path("/tmp/out")
    result = build_out_name(
        "musik.mp3",
        out_dir,
        template="{audio_stem}_{date}_{time}.mp4",
        now=now,
    )
    assert result == out_dir / "musik_20240102_030405.mp4"


def test_build_out_name_rejects_unknown_placeholder() -> None:
    with pytest.raises(ValueError):
        build_out_name("musik.mp3", Path("/tmp/out"), template="{unbekannt}.mp4")
