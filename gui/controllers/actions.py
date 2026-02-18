from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from core.ui_texts import text_with_fallback


@dataclass
class MainWindowState:
    """Kapselt veränderlichen GUI-Zustand ohne globale Streuung."""

    last_image_dir: Path
    last_audio_dir: Path
    last_project_file: Optional[Path] = None
    selected_images: List[str] = field(default_factory=list)
    selected_audios: List[str] = field(default_factory=list)


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
