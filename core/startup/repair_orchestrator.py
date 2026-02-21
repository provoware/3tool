from __future__ import annotations

from pathlib import Path
from typing import Iterable

from core import launcher_checks
from core.startup.bootstrap import all_blocking_ok, run_startup_checks


def _validate_startup_inputs(
    py: str, target_dir: Path, project_root: Path
) -> None:
    if not isinstance(py, str) or not py.strip():
        raise ValueError(
            "py muss ein nicht-leerer String sein. "
            "Naechster Schritt: Interpreter pruefen mit: python3 --version"
        )
    if not isinstance(target_dir, Path):
        raise TypeError("target_dir muss ein Path sein")
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein")


def _validate_check_results(
    results: Iterable[launcher_checks.CheckResult],
    stage_name: str,
) -> list[launcher_checks.CheckResult]:
    validated = list(results)
    if not validated:
        raise RuntimeError(
            f"{stage_name}: keine Pruefergebnisse erhalten. "
            "Naechster Schritt: Vollcheck starten mit: ./scripts/qa.sh"
        )
    for entry in validated:
        if not isinstance(entry, launcher_checks.CheckResult):
            raise RuntimeError(
                f"{stage_name}: ungueltiges Pruefergebnis erkannt. "
                "Naechster Schritt: Start-Checks debuggen mit: python3 -m app --mode checks --debug"
            )
    return validated


def apply_repairs(
    py: str,
    target_dir: Path,
    project_root: Path,
) -> tuple[
    list[launcher_checks.CheckResult], list[launcher_checks.RepairResult]
]:
    _validate_startup_inputs(py, target_dir, project_root)

    check_results = _validate_check_results(
        run_startup_checks(py, target_dir, project_root),
        "Start-Check vor Reparatur",
    )
    if all_blocking_ok(check_results):
        return check_results, []

    repairs = launcher_checks.run_repairs(py, target_dir, project_root)
    check_results = _validate_check_results(
        run_startup_checks(py, target_dir, project_root),
        "Start-Check nach Reparatur",
    )
    return check_results, repairs
