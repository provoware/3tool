from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from core import launcher_checks
from core.paths import cache_dir, config_dir, log_dir, user_data_dir, work_dir


class BootstrapError(RuntimeError):
    """Fehler im gemeinsamen Start-Bootstrap."""


@dataclass(frozen=True)
class BootstrapContext:
    project_root: Path
    python_cmd: str
    runtime_dirs: dict[str, Path]


def _fail(message: str) -> None:
    raise BootstrapError(message)


def ensure_required_files(
    project_root: Path, required_files: tuple[str, ...]
) -> None:
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")
    if not isinstance(required_files, tuple) or not required_files:
        _fail("Interner Fehler: required_files ist ungueltig.")
    missing = [
        name for name in required_files if not (project_root / name).exists()
    ]
    if missing:
        joined = ", ".join(missing)
        _fail(
            "Wichtige Projektdateien fehlen: "
            f"{joined}. Bitte Projekt erneut vollstaendig herunterladen."
        )


def prepare_runtime_dirs() -> dict[str, Path]:
    required_dirs = {
        "Nutzerdaten": user_data_dir(),
        "Konfiguration": config_dir(),
        "Protokolle": log_dir(),
        "Arbeitsdaten": work_dir(),
        "Cache": cache_dir(),
    }
    for name, target in required_dirs.items():
        target.mkdir(parents=True, exist_ok=True)
        if not launcher_checks.write_permissions_ok(target):
            _fail(
                f"Keine Schreibrechte in {target} ({name}). "
                "Bitte Ordnerrechte pruefen oder Home-Verzeichnis nutzen."
            )
    return required_dirs


def ensure_venv_python(project_root: Path) -> str:
    try:
        launcher_checks.ensure_venv(project_root)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        _fail(
            "Python-Umgebung konnte nicht vorbereitet werden: "
            f"{exc}. Befehl: python3 -m venv .videotool_env"
        )
    return str(launcher_checks.venv_python(project_root))


def run_preflight(py: str, user_data_path: Path, project_root: Path) -> None:
    checks = launcher_checks.collect_checks(py, user_data_path, project_root)
    if all(item.ok for item in checks if item.blocking):
        return

    repairs = launcher_checks.run_repairs(py, user_data_path, project_root)
    checks = launcher_checks.collect_checks(py, user_data_path, project_root)
    if all(item.ok for item in checks if item.blocking):
        return

    hints = launcher_checks.beginner_recovery_hints(repairs)
    hints_block = "\n".join(f" - {item}" for item in hints)
    _fail(
        "Start-Bootstrap fehlgeschlagen. "
        "Ursache: Abhaengigkeiten/Tools konnten nicht geprueft oder repariert werden. "
        "Naechster Schritt: Hinweise ausfuehren.\n"
        f"{hints_block}"
    )


def run_bootstrap(
    project_root: Path,
    required_files: tuple[str, ...],
    debug: bool,
) -> BootstrapContext:
    ensure_required_files(project_root, required_files)
    runtime_dirs = prepare_runtime_dirs()
    launcher_log = runtime_dirs["Protokolle"] / "launcher.log"
    launcher_checks.configure_logging(launcher_log, debug)
    py = ensure_venv_python(project_root)
    run_preflight(py, runtime_dirs["Nutzerdaten"], project_root)
    return BootstrapContext(
        project_root=project_root, python_cmd=py, runtime_dirs=runtime_dirs
    )
