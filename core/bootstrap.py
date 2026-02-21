from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

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


def run_preflight(  # noqa: C901
    py: str, user_data_path: Path, project_root: Path
) -> None:
    if not isinstance(py, str) or not py.strip():
        _fail(
            "Interner Fehler: python command ist leer. "
            "Naechster Schritt: Interpreter pruefen mit 'python3 --version'."
        )
    if not isinstance(user_data_path, Path):
        _fail("Interner Fehler: user_data_path ist kein Path.")
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")

    report_path = user_data_path / "logs" / "startup_preflight_report.json"

    def _emit_feedback(message: str) -> None:
        if not isinstance(message, str) or not message.strip():
            _fail("Interner Fehler: Rueckmeldungstext ist ungueltig.")
        print(message)

    def _summarize_checks(
        checks: list[launcher_checks.CheckResult],
        *,
        stage_name: str,
    ) -> str:
        total = len(checks)
        failed = len([item for item in checks if not item.ok])
        blocking_failed = len(
            [item for item in checks if item.blocking and not item.ok]
        )
        return (
            f"{stage_name}: {total} Pruefungen, {failed} mit Problem, "
            f"{blocking_failed} blockierend."
        )

    def _next_step_commands(
        checks: list[launcher_checks.CheckResult],
    ) -> list[str]:
        commands: list[str] = []
        for item in checks:
            if not item.ok and item.fix_hint:
                commands.append(item.fix_hint)
        return commands[:3]

    def _validate_checks(
        checks: list[launcher_checks.CheckResult],
        *,
        stage_name: str,
    ) -> list[launcher_checks.CheckResult]:
        if not checks:
            _fail(
                f"Interner Fehler: {stage_name} lieferte keine Ergebnisse. "
                "Naechster Schritt: Vollcheck starten mit './scripts/qa.sh'."
            )
        if any(
            not isinstance(item, launcher_checks.CheckResult) for item in checks
        ):
            _fail(
                f"Interner Fehler: {stage_name} lieferte ungueltige "
                "Pruefobjekte. Naechster Schritt: Start im Debug-Modus "
                "ausfuehren mit 'python3 app.py --mode gui --debug'."
            )
        return checks

    def _validate_repairs(
        repairs: list[launcher_checks.RepairResult],
    ) -> list[launcher_checks.RepairResult]:
        if any(
            not isinstance(item, launcher_checks.RepairResult)
            for item in repairs
        ):
            _fail(
                "Interner Fehler: Reparatur lieferte ungueltige Ergebnisse. "
                "Naechster Schritt: Reparatur erneut starten im Debug-Modus "
                "mit 'python3 app.py --mode gui --debug'."
            )
        return repairs

    def _serialize_checks(
        items: list[launcher_checks.CheckResult],
    ) -> list[dict[str, str | bool | None]]:
        return [
            {
                "key": item.key,
                "title": item.title,
                "ok": item.ok,
                "detail": item.detail,
                "fix_hint": item.fix_hint,
                "blocking": item.blocking,
            }
            for item in items
        ]

    def _write_report(
        *,
        status: str,
        checks_before: list[launcher_checks.CheckResult],
        checks_after: list[launcher_checks.CheckResult],
        repairs: list[launcher_checks.RepairResult],
    ) -> None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "python_cmd": py,
            "project_root": str(project_root),
            "report_path": str(report_path),
            "checks_before": _serialize_checks(checks_before),
            "checks_after": _serialize_checks(checks_after),
            "check_feedback": launcher_checks.build_check_feedback(
                checks_after or checks_before
            ),
            "repair_feedback": launcher_checks.build_repair_feedback(repairs),
            "beginner_hints": launcher_checks.beginner_recovery_hints(repairs),
            "next_actions": [
                "Debug-Modus aktivieren (erweiterte Protokolle): "
                "python3 app.py --mode gui --debug",
                "Kompletten Qualitaetslauf starten: ./scripts/qa.sh",
            ],
        }
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    checks = _validate_checks(
        launcher_checks.collect_checks(py, user_data_path, project_root),
        stage_name="Start-Checks vor Reparatur",
    )
    _emit_feedback(
        f"🔎 {_summarize_checks(checks, stage_name='Start-Analyse')}"
    )

    if all(item.ok for item in checks if item.blocking):
        _emit_feedback(
            "✅ System bereit. Naechster Schritt: Du kannst direkt mit der "
            "Bearbeitung starten."
        )
        _write_report(
            status="ok",
            checks_before=checks,
            checks_after=checks,
            repairs=[],
        )
        return

    _emit_feedback(
        "🛠️ Automatische Reparatur startet. Bitte kurz warten, "
        "fehlende Abhaengigkeiten werden selbststaendig korrigiert."
    )

    repairs = _validate_repairs(
        launcher_checks.run_repairs(py, user_data_path, project_root)
    )
    checks_after = _validate_checks(
        launcher_checks.collect_checks(py, user_data_path, project_root),
        stage_name="Start-Checks nach Reparatur",
    )
    _emit_feedback(
        f"🧪 {_summarize_checks(checks_after, stage_name='Kontrolle nach Reparatur')}"
    )
    if all(item.ok for item in checks_after if item.blocking):
        _emit_feedback(
            "✅ Reparatur erfolgreich. Naechster Schritt: Programm startet "
            "jetzt normal weiter."
        )
        _write_report(
            status="repaired",
            checks_before=checks,
            checks_after=checks_after,
            repairs=repairs,
        )
        return

    _write_report(
        status="failed",
        checks_before=checks,
        checks_after=checks_after,
        repairs=repairs,
    )

    hints = launcher_checks.beginner_recovery_hints(repairs)
    hints_block = "\n".join(f" - {item}" for item in hints)
    quick_commands = _next_step_commands(checks_after)
    command_block = "\n".join(f" - {item}" for item in quick_commands)
    if command_block:
        _emit_feedback(
            "⚠️ Einige Punkte brauchen noch manuelle Hilfe. "
            "Kopierbare Befehle:\n"
            f"{command_block}"
        )
    _fail(
        "Start-Bootstrap fehlgeschlagen. "
        "Ursache: Abhaengigkeiten/Tools konnten nicht geprueft oder repariert werden. "
        "Naechster Schritt: Hinweise ausfuehren.\n"
        f"{hints_block}\n"
        f"Ausfuehrlicher Report: {report_path}"
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
