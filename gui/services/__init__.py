from __future__ import annotations

from .project_io import (
    build_project_payload,
    load_project_file,
    make_project_relative,
    resolve_project_path,
    save_project_file,
)
from .runtime_paths import (
    build_default_runtime_paths,
    check_ffmpeg,
    safe_move,
    which,
)


def play_audio_preview(*args, **kwargs):
    from .preview import play_audio_preview as _play_audio_preview

    return _play_audio_preview(*args, **kwargs)


def stop_audio_preview(*args, **kwargs):
    from .preview import stop_audio_preview as _stop_audio_preview

    return _stop_audio_preview(*args, **kwargs)


__all__ = [
    "build_default_runtime_paths",
    "build_project_payload",
    "check_ffmpeg",
    "load_project_file",
    "make_project_relative",
    "play_audio_preview",
    "resolve_project_path",
    "safe_move",
    "save_project_file",
    "stop_audio_preview",
    "which",
]
