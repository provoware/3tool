from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from core.ui_texts import text_with_fallback
from gui.state import AudiosModel, ImagesModel, PairsModel


@dataclass
class MainWindowState:
    """Kapselt veränderlichen GUI-Zustand ohne globale Streuung."""

    last_image_dir: Path
    last_audio_dir: Path
    last_project_file: Optional[Path] = None
    images_model: ImagesModel = field(default_factory=ImagesModel)
    audios_model: AudiosModel = field(default_factory=AudiosModel)
    pairs_model: PairsModel = field(default_factory=PairsModel)

    @property
    def selected_images(self) -> list[str]:
        return self.images_model.items

    @selected_images.setter
    def selected_images(self, values: list[str]) -> None:
        self.images_model.set_items(values)

    @property
    def selected_audios(self) -> list[str]:
        return self.audios_model.items

    @selected_audios.setter
    def selected_audios(self, values: list[str]) -> None:
        self.audios_model.set_items(values)


def build_initial_state(
    last_image_dir: Path, last_audio_dir: Path
) -> MainWindowState:
    if not isinstance(last_image_dir, Path) or not isinstance(
        last_audio_dir, Path
    ):
        raise TypeError(
            "last_image_dir und last_audio_dir muessen Path-Objekte sein"
        )
    return MainWindowState(
        last_image_dir=last_image_dir, last_audio_dir=last_audio_dir
    )


def validate_project_root_candidate(path: Path) -> bool:
    if not isinstance(path, Path):
        return False
    return path.exists() and path.is_dir()


def resolve_text(
    texts: dict[str, str],
    key: str,
    fallback: str,
) -> str:
    if not isinstance(texts, dict):
        raise TypeError("texts muss ein Dict sein")
    return text_with_fallback(texts, key, fallback)
