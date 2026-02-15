from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

TOOL_MODULES: Final[dict[str, str]] = {
    "black": "black",
    "ruff": "ruff",
    "mypy": "mypy",
    "pytest": "pytest",
    "flake8": "flake8",
    "isort": "isort",
    "autoflake": "autoflake",
}


def _validate_requirements_path(path: Path) -> None:
    if not isinstance(path, Path):
        raise TypeError("path muss ein Path sein.")
    if not path.exists() or not path.is_file():
        raise ValueError(f"Requirements-Datei fehlt: {path}")


def _validate_tool_names(tool_names: list[str]) -> list[str]:
    if not isinstance(tool_names, list):
        raise TypeError("tool_names muss eine Liste sein.")
    cleaned: list[str] = []
    for name in tool_names:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                "Jeder Tool-Name muss ein nicht-leerer String sein."
            )
        normalized = name.strip()
        if normalized not in TOOL_MODULES:
            supported = ", ".join(sorted(TOOL_MODULES))
            raise ValueError(
                f"Unbekanntes Tool '{normalized}'. Erlaubt: {supported}"
            )
        cleaned.append(normalized)
    return cleaned


def _validate_python_cmd(python_cmd: str) -> str:
    if not isinstance(python_cmd, str):
        raise TypeError("python_cmd muss ein String sein.")
    interpreter = python_cmd.strip()
    if not interpreter:
        raise ValueError("python_cmd muss ein nicht-leerer String sein.")
    return interpreter


def _validate_debug_mode(debug_mode: bool) -> bool:
    if not isinstance(debug_mode, bool):
        raise TypeError("debug_mode muss ein bool sein.")
    return debug_mode


def _print_info(message: str) -> None:
    print(f"ℹ️  {message}")


def _print_ok(message: str) -> None:
    print(f"✅ {message}")


def _print_warn(message: str) -> None:
    print(f"⚠️  {message}")


def _print_debug(message: str, debug_mode: bool) -> None:
    if debug_mode:
        print(f"🐞 {message}")


def _run_pip_install(requirements: Path, python_cmd: str) -> None:
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "--upgrade", "pip"]
    )
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "-r", str(requirements)]
    )


def _module_import_ok(module_name: str, python_cmd: str) -> bool:
    return (
        subprocess.run(
            [python_cmd, "-c", f"import {module_name}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def run_preflight(
    requirements: Path,
    tool_names: list[str],
    python_cmd: str,
    debug_mode: bool = False,
) -> int:
    _validate_requirements_path(requirements)
    selected_tools = _validate_tool_names(tool_names)
    interpreter = _validate_python_cmd(python_cmd)
    debug_enabled = _validate_debug_mode(debug_mode)

    _print_ok(f"Requirements-Datei gefunden: {requirements}")
    _print_info(f"Validierte Prüftools: {', '.join(selected_tools)}")
    _print_debug(
        f"Debug-Modus aktiv. Interpreter-Kandidat: {interpreter}",
        debug_enabled,
    )

    if shutil.which(interpreter) is None:
        print(f"❌ Python-Interpreter nicht gefunden: {interpreter}")
        print("💡 Bitte Python installieren oder den Interpreterpfad prüfen.")
        return 1

    _print_ok(f"Python-Interpreter gefunden: {interpreter}")
    _print_info(f"Starte QA-Preflight mit {interpreter}")
    _print_debug(
        f"Installiere Abhängigkeiten aus: {requirements}",
        debug_enabled,
    )
    try:
        _run_pip_install(requirements, interpreter)
    except subprocess.SubprocessError as exc:
        print("❌ Abhängigkeiten konnten nicht vollständig installiert werden.")
        print(f"💡 Ursache: {exc}")
        print(
            "💡 Lösung: Internet, Rechte und Requirements-Datei prüfen; "
            f"Befehl manuell testen: {interpreter} -m pip install -r {requirements}"
        )
        return 1

    failed_tools: list[str] = []
    for tool in selected_tools:
        module_name = TOOL_MODULES[tool]
        _print_debug(
            f"Prüfe Tool-Import: {tool} (Modul: {module_name})",
            debug_enabled,
        )
        if _module_import_ok(module_name, interpreter):
            _print_ok(f"Tool bereit: {tool}")
        else:
            failed_tools.append(tool)
            _print_warn(f"Tool nicht importierbar: {tool}")

    if failed_tools:
        print(
            "❌ QA-Preflight unvollständig. Fehlende Tools: "
            + ", ".join(failed_tools)
        )
        print(
            "💡 Lösung: Starte erneut oder installiere manuell: "
            f"{interpreter} -m pip install --upgrade {' '.join(failed_tools)}"
        )
        return 1

    _print_ok(
        "QA-Preflight erfolgreich: alle benötigten Prüftools sind nutzbar."
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Bereitet QA-Prüftools vollautomatisch vor "
            "(Abhängigkeiten installieren + Tool-Importe verifizieren)."
        )
    )
    parser.add_argument(
        "--requirements",
        default="requirements-dev.txt",
        help="Pfad zur Dev-Requirements-Datei.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python-Interpreter für Installation und Prüfungen.",
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        default=["ruff", "black", "mypy", "pytest"],
        help="Zu validierende Prüftools.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Aktiviert detaillierte Fehlersuche (Debug-Modus) mit "
            "zusätzlichen Zwischenschritten für die Fehlersuche."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        return run_preflight(
            Path(args.requirements),
            args.tools,
            args.python,
            debug_mode=args.debug,
        )
    except (TypeError, ValueError) as exc:
        print(f"❌ Ungültige QA-Preflight-Eingabe: {exc}")
        print(
            "💡 Lösung: Dateipfade und Tool-Namen prüfen, "
            "z. B. --requirements requirements-dev.txt --tools ruff black"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
