from __future__ import annotations

from .output_preview import build_mini_preview_summary
from .project_io import (build_project_payload, load_project_file,
                         make_project_relative, resolve_project_path,
                         save_project_file)
from .runtime_paths import (build_default_runtime_paths, check_ffmpeg,
                            safe_move, which)
from .workflow_services import ExportService, PairingService, ValidationService


def play_audio_preview(*args, **kwargs):
    from .preview import play_audio_preview as _play_audio_preview

    return _play_audio_preview(*args, **kwargs)


def stop_audio_preview(*args, **kwargs):
    from .preview import stop_audio_preview as _stop_audio_preview

    return _stop_audio_preview(*args, **kwargs)


__all__ = [
    "ExportService",
    "PairingService",
    "ValidationService",
    "build_default_runtime_paths",
    "build_project_payload",
    "check_ffmpeg",
    "load_project_file",
    "make_project_relative",
    "build_mini_preview_summary",
    "play_audio_preview",
    "resolve_project_path",
    "safe_move",
    "save_project_file",
    "stop_audio_preview",
    "which",
]
