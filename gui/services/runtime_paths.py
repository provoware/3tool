from __future__ import annotations

import shutil
from pathlib import Path

from core.output_management import transfer_with_validation
from gui.state.runtime_state import RuntimePaths


def which(binary_name: str) -> str | None:
    if not isinstance(binary_name, str) or not binary_name.strip():
        raise ValueError("binary_name muss ein nicht-leerer String sein")
    return shutil.which(binary_name.strip())


def check_ffmpeg() -> bool:
    return bool(which("ffmpeg") and which("ffprobe"))


def build_default_runtime_paths(home: Path | None = None) -> RuntimePaths:
    home_dir = home if isinstance(home, Path) else Path.home()
    downloads = home_dir / "Downloads"
    return RuntimePaths(
        used_dir=home_dir / "benutzte_dateien",
        output_dir=home_dir / "Videos" / "VideoBatchTool_Out",
        project_dir=home_dir / "VideoBatchTool_Projekte",
        downloads_dir=downloads if downloads.exists() else home_dir,
    )


def safe_move(src: Path, dst_dir: Path, copy_only: bool = False) -> Path:
    result = transfer_with_validation(
        src,
        dst_dir,
        copy_only=copy_only,
        suffix_label="benutzt",
    )
    if not result.validated:
        raise IOError(result.detail)
    return result.target
