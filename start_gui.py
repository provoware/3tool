from __future__ import annotations

import argparse
import importlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Callable, NoReturn, cast

from core import launcher_checks
from core.config import apply_simple_mode_defaults, cfg
from core.paths import cache_dir, config_dir, log_dir, user_data_dir, work_dir

REQUIRED_FILES = ("videobatch_gui.py", "videobatch_extra.py")
PROJECT_ROOT = Path(__file__).resolve().parent


class LauncherError(RuntimeError):
    """User-friendly launcher error."""


def _status(step: int, total: int, title: str) -> None:
    print(f"[{step}/{total}] {title}")


def _ok(message: str) -> None:
    print(f"  ✅ {message}")


def _warn(message: str) -> None:
    print(f"  ⚠️  {message}")


def _fail(message: str) -> NoReturn:
    raise LauncherError(message)


def _ensure_files(project_root: Path = PROJECT_ROOT) -> None:
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")
    missing = [
        name for name in REQUIRED_FILES if not (project_root / name).exists()
    ]
    if missing:
        _fail(
            "Wichtige Projektdateien fehlen: "
            + ", ".join(missing)
            + ". Bitte Projekt vollständig entpacken oder neu klonen."
        )


def _import_module(name: str, project_root: Path = PROJECT_ROOT):
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")
    root = str(project_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        return importlib.import_module(name)
    except (
        ImportError,
        ModuleNotFoundError,
        ValueError,
    ) as exc:  # pragma: no cover - user facing runtime guard
        _fail(
            f"Start-Modul '{name}' konnte nicht geladen werden. "
            "Ursache: Abhängigkeit fehlt oder Modul ist defekt. "
            "Nächster Schritt: automatische Reparatur starten. "
            "Befehl: python3 videobatch_extra.py --self-repair --debug"
            f"\nTechnik-Detail: {exc}"
        )


def _prepare_runtime_dirs() -> dict[str, Path]:
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
                "Bitte Ordnerrechte prüfen oder anderen Benutzerordner nutzen."
            )
    return required_dirs


def _validated_runtime_dirs(
    runtime_dirs: dict[str, Path], required_keys: tuple[str, ...]
) -> dict[str, Path]:
    if not isinstance(runtime_dirs, dict):
        _fail("Interner Fehler: runtime_dirs ist kein Dictionary.")
    validated: dict[str, Path] = {}
    for key in required_keys:
        value = runtime_dirs.get(key)
        if not isinstance(value, Path):
            _fail(
                "Interner Fehler: Laufzeitordner fehlt oder ist ungültig "
                f"({key})."
            )
        validated[key] = runtime_dirs[key]
    return validated


def _safe_prepare_runtime_dirs() -> dict[str, Path]:
    try:
        runtime_dirs = _prepare_runtime_dirs()
    except OSError as exc:
        _fail(
            "Laufzeitordner konnten nicht erstellt werden: "
            f"{exc}. Bitte Rechte/Speicherplatz prüfen."
        )
    return _validated_runtime_dirs(runtime_dirs, ("Nutzerdaten", "Protokolle"))


def _safe_ensure_venv(project_root: Path = PROJECT_ROOT) -> str:
    try:
        launcher_checks.ensure_venv(project_root)
        return str(launcher_checks.venv_python(project_root))
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        _fail(
            "Python-Umgebung konnte nicht vorbereitet werden: "
            f"{exc}. Bitte 'python3 -m venv .videotool_env' ausführen."
        )


def _safe_run_checks(
    py: str, target_dir: Path, project_root: Path = PROJECT_ROOT
) -> list[launcher_checks.CheckResult]:
    try:
        return _run_checks(py, target_dir, project_root)
    except (TypeError, ValueError, OSError) as exc:
        _fail(
            "System-Checks konnten nicht abgeschlossen werden: "
            f"{exc}. Bitte Debug-Modus starten (python3 start_gui.py --debug)."
        )


def _print_release_readiness(project_root: Path) -> bool:
    checks = launcher_checks.evaluate_release_readiness(project_root)
    print("\nRelease-Check (was fehlt bis zur Freigabe?):")
    for item in checks:
        marker = "✅" if item.ok else "⚠️"
        print(f"  {marker} {item.title}: {item.detail}")
        if not item.ok:
            print(f"     Nächster Schritt: {item.recommendation}")
    blocking_ok = all(item.ok for item in checks if item.blocking)
    if blocking_ok:
        print("  ✅ Release-Basis erfüllt (technisch).")
    else:
        print(
            "  ⚠️  Release noch nicht bereit: offene Punkte bitte vor Freigabe lösen."
        )
    return blocking_ok


def _print_beginner_tips() -> None:
    print("\nLaien-Tipps (einfach):")
    print(" - Bei Problemen zuerst: python3 start_gui.py --auto-repair")
    print(" - Für schwächere Geräte: python3 start_gui.py --simple-mode")
    print(" - Details/Fehlerbericht: python3 start_gui.py --debug")
    print(" - Selbsttest für CLI: python3 videobatch_extra.py --selftest")


def _run_release_quality_check(project_root: Path) -> bool:
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")

    quality_script = project_root / "scripts" / "quality_check.sh"
    if not quality_script.exists():
        _warn(
            "Release-Qualitätscheck nicht gefunden "
            f"({quality_script}). Überspringe diesen Schritt."
        )
        return False

    cmd = ["bash", str(quality_script)]
    print("  🔎 Starte Release-Qualitätscheck (scripts/quality_check.sh)")
    launcher_checks.LOGGER.info("Release-Qualitätscheck gestartet: %s", cmd)
    completed = subprocess.run(
        cmd,
        cwd=project_root,
        check=False,
        timeout=900,
    )
    if completed.returncode == 0:
        _ok("Release-Qualitätscheck erfolgreich abgeschlossen")
        return True

    _warn(
        "Release-Qualitätscheck meldet Probleme. "
        "GUI-Start läuft weiter, bitte vor Release beheben."
    )
    print(
        "  💡 Vorschlag: Erst 'scripts/quality_fix.sh' ausführen, "
        "dann 'scripts/quality_check.sh' wiederholen."
    )
    return False


def _run_checks(
    py: str, target_dir: Path, project_root: Path = PROJECT_ROOT
) -> list[launcher_checks.CheckResult]:
    results = launcher_checks.collect_checks(py, target_dir, project_root)
    for result in results:
        marker = "✅" if result.ok else "❌"
        print(f"  {marker} {result.title}: {result.detail}")
        if not result.ok and result.fix_hint:
            print(f"     Tipp: {result.fix_hint}")
    return results


def _print_check_summary(results: list[launcher_checks.CheckResult]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item.ok)
    failed = total - passed
    blocking_failed = sum(
        1 for item in results if item.blocking and not item.ok
    )
    print(
        "  📋 Check-Zusammenfassung: "
        f"{passed}/{total} ok, {failed} problematisch, "
        f"{blocking_failed} blockierend"
    )


def _all_blocking_ok(results: list[launcher_checks.CheckResult]) -> bool:
    return all(result.ok for result in results if result.blocking)


def _print_feedback_block(feedback: launcher_checks.CheckFeedback) -> None:
    if not isinstance(feedback, dict):
        _fail("Interner Fehler: feedback ist kein Dictionary.")

    print(f"  🧾 {feedback['headline']} | {feedback['summary']}")
    next_steps = feedback.get("next_steps", [])
    if isinstance(next_steps, list) and next_steps:
        print("  👉 Nächste Schritte:")
        for step in next_steps:
            print(f"     - {step}")

    beginner_terms = feedback.get("beginner_terms", [])
    if isinstance(beginner_terms, list) and beginner_terms:
        print("  📘 Kurz erklärt:")
        for term in beginner_terms:
            print(f"     - {term}")

    quick_commands = feedback.get("quick_commands", [])
    if isinstance(quick_commands, list) and quick_commands:
        print("  ⚙️ Schnellbefehle:")
        for command in quick_commands:
            print(f"     - {command}")


def _dependency_bootstrap(
    py: str, target_dir: Path, project_root: Path = PROJECT_ROOT
) -> list[launcher_checks.CheckResult]:
    if not isinstance(target_dir, Path):
        _fail("Interner Fehler: target_dir ist kein Path.")
    if not isinstance(project_root, Path):
        _fail("Interner Fehler: project_root ist kein Path.")

    print("  🔄 Präventiver Start-Bootstrap: Prüfungen und Auto-Reparatur")
    results = _safe_run_checks(py, target_dir, project_root)
    _print_check_summary(results)
    _print_feedback_block(launcher_checks.build_check_feedback(results))

    if _all_blocking_ok(results):
        launcher_checks.LOGGER.info(
            "Bootstrap abgeschlossen: alle Pflichtpruefungen erfolgreich."
        )
        return results

    _warn(
        "Pflichtpruefungen nicht bestanden. Starte automatische Reparatur "
        "mit laienfreundlichem Feedback."
    )
    repairs = _safe_run_repairs(py, target_dir, project_root)
    repair_feedback = launcher_checks.build_repair_feedback(repairs)
    print(
        "  🛠️ " f"{repair_feedback['headline']} | {repair_feedback['summary']}"
    )
    for hint in repair_feedback.get("hints", []):
        print(f"     - {hint}")

    print("  🔁 Wiederhole Pflichtprüfungen nach Reparatur")
    results = _safe_run_checks(py, target_dir, project_root)
    _print_check_summary(results)
    _print_feedback_block(launcher_checks.build_check_feedback(results))

    if not _all_blocking_ok(results):
        _fail(
            "Start abgebrochen: Umgebung ist noch nicht bereit. "
            "Bitte Hinweise oben ausführen und erneut starten."
        )

    launcher_checks.LOGGER.info(
        "Bootstrap erfolgreich: Pflichtpruefungen nach Reparatur erfolgreich."
    )
    return results


def _run_repairs(
    py: str, target_dir: Path, project_root: Path = PROJECT_ROOT
) -> list[launcher_checks.RepairResult]:
    repairs = launcher_checks.run_repairs(py, target_dir, project_root)
    for repair in repairs:
        marker = "✅" if repair.ok else "❌"
        print(f"  {marker} {repair.title}: {repair.detail}")
        launcher_checks.LOGGER.info(
            "Repair %s (%s): %s",
            "ok" if repair.ok else "failed",
            repair.key,
            repair.detail,
        )
    success = sum(1 for item in repairs if item.ok)
    failed = len(repairs) - success
    print(
        "  🛠️ Repair-Zusammenfassung: "
        f"{success}/{len(repairs)} erfolgreich, {failed} fehlgeschlagen"
    )
    hints = launcher_checks.beginner_recovery_hints(repairs)
    if hints:
        print("  🧭 Einfache Loesungsvorschlaege:")
        for hint in hints:
            print(f"     - {hint}")
    return repairs


def _safe_run_repairs(
    py: str, target_dir: Path, project_root: Path = PROJECT_ROOT
) -> list[launcher_checks.RepairResult]:
    try:
        return _run_repairs(py, target_dir, project_root)
    except (TypeError, ValueError, OSError) as exc:
        _fail(
            "Self-Repair konnte nicht abgeschlossen werden: "
            f"{exc}. Bitte erneut mit --debug starten."
        )


def _start_gui(start_func: Callable[[], None]) -> None:
    try:
        start_func()
    except (
        RuntimeError,
        OSError,
        subprocess.SubprocessError,
    ) as exc:  # pragma: no cover - user facing runtime guard
        logging.getLogger(__name__).exception(
            "launcher.gui_start_failed",
            extra={"error": str(exc)},
        )
        _fail(
            "Die Oberfläche konnte nicht gestartet werden. "
            "Ursache: Systembibliothek oder Tool fehlt/ist blockiert. "
            "Nächster Schritt: Selbsttest ausführen und Hinweise befolgen. "
            "Befehl: python3 videobatch_extra.py --selftest"
            f"\nTechnik-Detail: {exc}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Klick-Start für VideoBatchTool mit Checks und Self-Repair"
    )
    parser.add_argument(
        "--auto-repair",
        action="store_true",
        help="führt Reparaturen automatisch aus, wenn Checks fehlschlagen",
    )
    parser.add_argument(
        "--simple-mode",
        action="store_true",
        help="ressourcenschonende Standardwerte (720p, CRF 24, veryfast)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="ausführliche Konsolenmeldungen aktivieren",
    )
    parser.add_argument(
        "--release-check",
        action="store_true",
        help=(
            "führt zusätzlich scripts/quality_check.sh aus "
            "(empfohlen vor einem Release)"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg.debug = args.debug

    steps = 7
    _status(1, steps, "Projektdateien prüfen")
    _ensure_files(PROJECT_ROOT)
    _ok("Projektdateien vollständig")

    _status(2, steps, "Laufzeitordner vorbereiten")
    runtime_dirs = _safe_prepare_runtime_dirs()
    launcher_log = runtime_dirs["Protokolle"] / "launcher.log"
    launcher_checks.configure_logging(launcher_log, args.debug)
    launcher_checks.LOGGER.info("Launcher gestartet (debug=%s)", args.debug)
    _ok("Daten-, Config-, Log-, Work- und Cache-Ordner bereit")

    _status(3, steps, "Launcher-Umgebung vorbereiten")
    py = _safe_ensure_venv(PROJECT_ROOT)
    _ok(f"Python-Umgebung bereit: {py}")

    _status(4, steps, "Präventiven Start-Bootstrap ausführen")
    _dependency_bootstrap(py, runtime_dirs["Nutzerdaten"], PROJECT_ROOT)

    if args.simple_mode:
        _status(6, steps, "Simple-Modus aktivieren")
        apply_simple_mode_defaults()
        _ok("Simple-Modus aktiv: 1280x720, CRF 24, Preset veryfast")

    _print_release_readiness(PROJECT_ROOT)
    if getattr(args, "release_check", False):
        _status(7, steps, "Release-Qualitätscheck ausführen")
        try:
            _run_release_quality_check(PROJECT_ROOT)
        except (OSError, subprocess.SubprocessError) as exc:
            _warn(
                "Release-Qualitätscheck konnte nicht vollständig laufen: "
                f"{exc}"
            )
            print(
                "  💡 Vorschlag: Manuell im Projektordner ausführen: "
                "bash scripts/quality_check.sh"
            )
    _print_beginner_tips()

    _status(steps, steps, "GUI starten")
    gui = _import_module("videobatch_gui", PROJECT_ROOT)
    start_func = getattr(gui, "run_gui", None)
    if not callable(start_func):
        _fail("videobatch_gui.run_gui fehlt. Bitte Projektdateien prüfen.")
    _start_gui(cast(Callable[[], None], start_func))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LauncherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(1)
