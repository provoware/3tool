from pathlib import Path

import pytest

from gui.controllers.actions import build_initial_state
from gui.services import ExportService, PairingService, ValidationService
from gui.state import PairRecord


def test_main_window_state_uses_models() -> None:
    state = build_initial_state(Path("/tmp/a"), Path("/tmp/b"))
    state.selected_images = [" /tmp/image.jpg "]
    state.selected_audios = ["/tmp/audio.mp3"]

    assert state.images_model.items == ["/tmp/image.jpg"]
    assert state.audios_model.items == ["/tmp/audio.mp3"]


def test_pairing_service_builds_pairs() -> None:
    pairs = PairingService.build_pairs(
        ["/tmp/one.png", "/tmp/two.png"],
        ["/tmp/one.mp3"],
    )
    assert len(pairs) == 1
    assert isinstance(pairs[0], PairRecord)


def test_export_service_build_export_targets(tmp_path: Path) -> None:
    source_pairs = [
        PairRecord(image_path="/tmp/image-a.png", audio_path="/tmp/audio-a.mp3")
    ]
    export_pairs = ExportService.build_export_targets(
        source_pairs,
        output_dir=tmp_path,
    )
    assert export_pairs[0].output_path == str(tmp_path / "image-a.mp4")


def test_validation_service_requires_existing_paths(tmp_path: Path) -> None:
    file_path = tmp_path / "x.txt"
    file_path.write_text("ok", encoding="utf-8")
    normalized = ValidationService.validate_existing_paths(
        [str(file_path)],
        field_name="Bilder",
    )
    assert normalized == [str(file_path)]

    with pytest.raises(ValueError):
        ValidationService.validate_existing_paths(
            [str(tmp_path / "missing.txt")],
            field_name="Bilder",
        )
