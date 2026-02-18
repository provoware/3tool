from pathlib import Path

import pytest

import videobatch_professional as prof


def test_normalize_threads_rejects_non_positive() -> None:
    with pytest.raises(ValueError):
        prof._normalize_threads(0)


def test_load_manifest_validates_mode(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '[{"mode": "bad", "source": "a.mp4", "audio": "b.mp3"}]',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        prof._load_manifest(manifest)


def test_run_job_reports_missing_source(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    result = prof._run_job(
        {
            "mode": "video",
            "source": str(tmp_path / "missing.mp4"),
            "audio": str(tmp_path / "audio.mp3"),
        },
        out_dir,
    )
    assert result["ok"] is False
    assert "Quelldatei fehlt" in str(result.get("error", ""))


def test_run_job_rejects_invalid_mode(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    audio = tmp_path / "audio.mp3"
    source.write_text("ok", encoding="utf-8")
    audio.write_text("ok", encoding="utf-8")

    result = prof._run_job(
        {
            "mode": "invalid",
            "source": str(source),
            "audio": str(audio),
        },
        tmp_path / "out",
    )

    assert result["ok"] is False
    assert "Ungueltiger Modus" in str(result.get("error", ""))
