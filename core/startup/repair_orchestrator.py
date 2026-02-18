from __future__ import annotations

from pathlib import Path

from core import launcher_checks
from core.startup.bootstrap import all_blocking_ok, run_startup_checks


def apply_repairs(
    py: str,
    target_dir: Path,
    project_root: Path,
) -> tuple[
    list[launcher_checks.CheckResult], list[launcher_checks.RepairResult]
]:
    check_results = run_startup_checks(py, target_dir, project_root)
    if all_blocking_ok(check_results):
        return check_results, []

    repairs = launcher_checks.run_repairs(py, target_dir, project_root)
    check_results = run_startup_checks(py, target_dir, project_root)
    return check_results, repairs
