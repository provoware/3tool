from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Callable

from core import launcher_checks
from core.config import apply_simple_mode_defaults, cfg
from core.paths import cache_dir, config_dir, log_dir, user_data_dir, work_dir

REQUIRED_FILES = ("videobatch_gui.py", "videobatch_extra.py")


class LauncherError(RuntimeError):
    """User-friendly launcher error."""


def _status(step: int, total: int, title: str) -> None:
    print(f"[{step}/{total}] {title}")


def _ok(message: str) -> None:
    print(f"  ✅ {message}")


def _warn(message: str) -> None:
    print(f"  ⚠️  {message}")


def _fail(message: str) -> None:
    raise LauncherError(message)


def _ensure_files() -> None:
    missing = [name for name in REQUIRED_FILES if not Path(name).exists()]
    if missing:
        _fail(
            "Wichtige Projektdateien fehlen: "
            + ", ".join(missing)
            + ". Bitte Projekt vollständig entpacken oder neu klonen."
        )


def _import_module(name: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - user facing runtime guard
        _fail(
            f"Modul '{name}' konnte nicht geladen werden: {exc}. "
            "Bitte Self-Repair ausführen oder Abhängigkeiten prüfen."
        )


def _prepare_runtime_dirs() -> None:
    required_dirs = (user_data_dir, config_dir, log_dir, work_dir, cache_dir)
    for dir_func in required_dirs:
        target = dir_func()
        target.mkdir(parents=True, exist_ok=True)
        if not launcher_checks.write_permissions_ok(target):
            _fail(
                f"Keine Schreibrechte in {target}. "
                "Bitte Ordnerrechte prüfen oder anderen Benutzerordner nutzen."
            )


def _print_beginner_tips() -> None:
    print("\nLaien-Tipps (einfach):")
    print(" - Bei Problemen zuerst: python3 start_gui.py --auto-repair")
    print(" - Für schwächere Geräte: python3 start_gui.py --simple-mode")
    print(" - Selbsttest für CLI: python3 videobatch_extra.py --selftest")


def _run_checks(py: str, target_dir: Path) -> list[launcher_checks.CheckResult]:
    results = launcher_checks.collect_checks(py, target_dir)
    for result in results:
        marker = "✅" if result.ok else "❌"
        print(f"  {marker} {result.title}: {result.detail}")
        if not result.ok and result.fix_hint:
            print(f"     Tipp: {result.fix_hint}")
    return results


def _all_blocking_ok(results: list[launcher_checks.CheckResult]) -> bool:
    return all(result.ok for result in results if result.blocking)


def _run_repairs(py: str, target_dir: Path) -> None:
    repairs = launcher_checks.run_repairs(py, target_dir)
    for repair in repairs:
        marker = "✅" if repair.ok else "❌"
        print(f"  {marker} {repair.title}: {repair.detail}")


def _start_gui(start_func: Callable[[], None]) -> None:
    try:
        start_func()
    except Exception as exc:  # pragma: no cover - user facing runtime guard
        _fail(
            f"GUI-Start fehlgeschlagen: {exc}. "
            "Bitte 'python3 videobatch_extra.py --selftest' ausführen."
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cfg.debug = args.debug

    steps = 7
    _status(1, steps, "Projektdateien prüfen")
    _ensure_files()
    _ok("Projektdateien vollständig")

    _status(2, steps, "Laufzeitordner vorbereiten")
    _prepare_runtime_dirs()
    _ok("Daten-, Config-, Log-, Work- und Cache-Ordner bereit")

    _status(3, steps, "Launcher-Umgebung vorbereiten")
    launcher_checks.ensure_venv()
    py = str(launcher_checks.venv_python())
    _ok(f"Python-Umgebung bereit: {py}")

    _status(4, steps, "System-Checks ausführen")
    results = _run_checks(py, user_data_dir())

    if not _all_blocking_ok(results):
        if args.auto_repair:
            _status(5, steps, "Self-Repair ausführen")
            _run_repairs(py, user_data_dir())
            _status(6, steps, "Checks nach Reparatur wiederholen")
            results = _run_checks(py, user_data_dir())
        else:
            _warn("Blockierende Probleme gefunden. Starte mit --auto-repair.")

    if not _all_blocking_ok(results):
        _fail(
            "Start abgebrochen: Umgebung ist noch nicht bereit. "
            "Bitte Hinweise oben ausführen und erneut starten."
        )

    if args.simple_mode:
        _status(6, steps, "Simple-Modus aktivieren")
        apply_simple_mode_defaults()
        _ok("Simple-Modus aktiv: 1280x720, CRF 24, Preset veryfast")

    _print_beginner_tips()

    _status(steps, steps, "GUI starten")
    gui = _import_module("videobatch_gui")
    start_func = getattr(gui, "run_gui", None)
    if not callable(start_func):
        _fail("videobatch_gui.run_gui fehlt. Bitte Projektdateien prüfen.")
    _start_gui(start_func)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LauncherError as exc:
        print(f"❌ {exc}")
        raise SystemExit(1)
