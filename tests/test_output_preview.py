from __future__ import annotations

from dataclasses import dataclass

from gui.services.output_preview import build_mini_preview_summary


@dataclass
class DummyPair:
    image_path: str
    audio_path: str | None
    output: str = ""


def test_output_preview_flags_missing_inputs_and_duplicates() -> None:
    pairs = [
        DummyPair(image_path="/tmp/a.jpg", audio_path="/tmp/a.mp3", output=""),
        DummyPair(image_path="", audio_path="/tmp/b.mp3", output=""),
        DummyPair(
            image_path="/tmp/c.jpg",
            audio_path="/tmp/c.mp3",
            output="/tmp/out/same.mp4",
        ),
        DummyPair(
            image_path="/tmp/d.jpg",
            audio_path="/tmp/d.mp3",
            output="/tmp/out/same.mp4",
        ),
    ]

    summary = build_mini_preview_summary(pairs, "/tmp/out", max_lines=5)

    assert summary.total_rows == 4
    assert summary.ready_rows == 2
    assert summary.conflict_rows == (1, 3)
    assert any("fehlt Bild" in line for line in summary.lines)
    assert any("Konflikt" in line for line in summary.lines)


def test_output_preview_respects_line_limit() -> None:
    pairs = [
        DummyPair(image_path=f"/tmp/{i}.jpg", audio_path=f"/tmp/{i}.mp3", output="")
        for i in range(6)
    ]

    summary = build_mini_preview_summary(pairs, "/tmp/out", max_lines=2)

    assert summary.total_rows == 6
    assert summary.ready_rows == 6
    assert summary.conflict_rows == ()
    assert len(summary.lines) == 2
