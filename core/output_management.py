from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .utils import linux_safe_stem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TransferResult:
    source: Path
    target: Path
    validated: bool
    action: str
    detail: str


def validate_directory(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("Pfad muss als Path übergeben werden.")
    resolved = path.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def classify_output_category(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if "audio" in normalized or "audios" in normalized:
        return "musik"
    if "slideshow" in normalized or "diashow" in normalized:
        return "tracks"
    return "tracks"


def build_dated_output_dir(
    base_output_dir: Path, mode: str, now: datetime | None = None
) -> Path:
    safe_base = validate_directory(base_output_dir)
    current = now or datetime.now()
    date_folder = current.strftime("%Y-%m-%d")
    category_folder = classify_output_category(mode)
    output_dir = safe_base / date_folder / category_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _build_target_path(
    source: Path, destination_dir: Path, suffix_label: str
) -> Path:
    stem = linux_safe_stem(source.stem, "datei")
    suffix = source.suffix.lower() or ".dat"
    target = destination_dir / f"{stem}_{suffix_label}{suffix}"
    if target.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = destination_dir / f"{stem}_{suffix_label}_{timestamp}{suffix}"
    return target


def transfer_with_validation(
    source: Path,
    destination_dir: Path,
    *,
    copy_only: bool,
    suffix_label: str,
) -> TransferResult:
    if not isinstance(source, Path):
        raise TypeError("Quelle muss als Path übergeben werden.")
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Quelldatei fehlt oder ist ungültig: {source}")
    destination = validate_directory(destination_dir)
    target = _build_target_path(source, destination, suffix_label)

    action = "kopiert" if copy_only else "verschoben"
    if copy_only:
        shutil.copy2(source, target)
    else:
        try:
            shutil.move(source, target)
        except (shutil.Error, OSError) as exc:
            logger.warning(
                "transfer.move_failed_fallback_copy",
                extra={
                    "source": str(source),
                    "target": str(target),
                    "error": str(exc),
                },
            )
            shutil.copy2(source, target)
            source.unlink(missing_ok=True)

    target_exists = target.exists() and target.is_file()
    source_size = (
        source.stat().st_size if source.exists() else target.stat().st_size
    )
    target_size = target.stat().st_size if target_exists else -1
    validated = target_exists and source_size == target_size
    detail = (
        f"Transfer ok ({action}). Größe: {target_size} Byte."
        if validated
        else "Transfer unvollständig: Datei oder Größe stimmt nicht."
    )
    return TransferResult(
        source=source,
        target=target,
        validated=validated,
        action=action,
        detail=detail,
    )
