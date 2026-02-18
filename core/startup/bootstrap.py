from __future__ import annotations

from pathlib import Path
from typing import Iterable

from core import launcher_checks
from core.paths import cache_dir, config_dir, log_dir, user_data_dir, work_dir

REQUIRED_FILES = ("videobatch_gui.py", "videobatch_extra.py")


def ensure_project_files(project_root: Path) -> list[str]:
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein")
    return [name for name in REQUIRED_FILES if not (project_root / name).exists()]


def prepare_runtime_dirs() -> dict[str, Path]:
    runtime_dirs = {
        "Nutzerdaten": user_data_dir(),
        "Konfiguration": config_dir(),
        "Protokolle": log_dir(),
        "Arbeitsdaten": work_dir(),
        "Cache": cache_dir(),
    }
    for target in runtime_dirs.values():
        target.mkdir(parents=True, exist_ok=True)
    return runtime_dirs


def run_startup_checks(
    py: str,
    target_dir: Path,
    project_root: Path,
) -> list[launcher_checks.CheckResult]:
    if not isinstance(target_dir, Path):
        raise TypeError("target_dir muss ein Path sein")
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein")
    return launcher_checks.collect_checks(py, target_dir, project_root)


def all_blocking_ok(results: Iterable[launcher_checks.CheckResult]) -> bool:
    result_list = list(results)
    return all(item.ok for item in result_list if item.blocking)
