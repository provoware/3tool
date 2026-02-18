from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
)
AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".m4a", ".aac")


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    message: str = ""


def validate_media_pair(
    image_path: Optional[str],
    audio_path: Optional[str],
) -> ValidationResult:
    image = (image_path or "").strip()
    audio = (audio_path or "").strip()
    if not image or not audio:
        return ValidationResult(False, "Bild oder Audio fehlt")

    image_file = Path(image)
    audio_file = Path(audio)

    if not image_file.exists():
        return ValidationResult(False, "Bildpfad nicht gefunden")
    if not audio_file.exists():
        return ValidationResult(False, "Audiopfad nicht gefunden")

    if image_file.is_dir():
        if not os.access(image_file, os.R_OK | os.X_OK):
            return ValidationResult(
                False,
                "Bildordner ist nicht lesbar (keine Rechte)",
            )
    else:
        if not os.access(image_file, os.R_OK):
            return ValidationResult(
                False,
                "Bilddatei ist nicht lesbar (keine Rechte)",
            )
        if image_file.suffix.lower() not in IMAGE_EXTENSIONS:
            return ValidationResult(False, "Ungültiges Bild- oder Videoformat")

    if not os.access(audio_file, os.R_OK):
        return ValidationResult(False, "Audiodatei ist nicht lesbar (keine Rechte)")
    if audio_file.suffix.lower() not in AUDIO_EXTENSIONS:
        return ValidationResult(False, "Ungültiges Audioformat")

    return ValidationResult(True, "")
