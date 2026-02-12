from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple


def _copy_if_valid(
    source: str, target_dir: Path, suffixes: Tuple[str, ...]
) -> str:
    src = Path((source or "").strip())
    if not src.is_file() or src.suffix.lower() not in suffixes:
        return ""
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / src.name
    if target.exists() and target.resolve() != src.resolve():
        target = target_dir / f"{src.stem}_fallback{src.suffix.lower()}"
    shutil.copy2(src, target)
    return str(target)


def persist_fallback_media(
    media_root: Path,
    image_path: str,
    audio_paths: Iterable[str],
) -> Tuple[str, List[str]]:
    image = _copy_if_valid(
        image_path,
        media_root / "images",
        (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4", ".mov"),
    )
    persisted_audio: List[str] = []
    for raw_audio in audio_paths:
        copied = _copy_if_valid(
            raw_audio,
            media_root / "audios",
            (".mp3", ".wav", ".flac", ".m4a", ".aac"),
        )
        if copied:
            persisted_audio.append(copied)
        if len(persisted_audio) >= 2:
            break
    return image, persisted_audio


def dumps_audio_list(audio_paths: Iterable[str]) -> str:
    clean = [str(Path(path)) for path in audio_paths if str(path).strip()]
    return json.dumps(clean, ensure_ascii=False)


def loads_audio_list(raw_value: str) -> List[str]:
    if not raw_value:
        return []
    try:
        values = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(values, list):
        return []
    return [str(Path(item)) for item in values if isinstance(item, str)]
