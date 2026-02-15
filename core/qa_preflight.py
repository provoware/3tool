from __future__ import annotations

import argparse
import socket
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

PIP_TIMEOUT_SECONDS: Final[int] = 300
IMPORT_TIMEOUT_SECONDS: Final[int] = 20
NETWORK_TIMEOUT_SECONDS: Final[int] = 3


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


def _validate_timeout_seconds(timeout_seconds: int, name: str) -> int:
    if not isinstance(timeout_seconds, int):
        raise TypeError(f"{name} muss ein int sein.")
    if timeout_seconds <= 0:
        raise ValueError(f"{name} muss groesser als 0 sein.")
    return timeout_seconds


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
    timeout_seconds = _validate_timeout_seconds(
        PIP_TIMEOUT_SECONDS,
        "PIP_TIMEOUT_SECONDS",
    )
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "--upgrade", "pip"],
        timeout=timeout_seconds,
    )
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "-r", str(requirements)],
        timeout=timeout_seconds,
    )


def _run_pip_install_user(requirements: Path, python_cmd: str) -> None:
    timeout_seconds = _validate_timeout_seconds(
        PIP_TIMEOUT_SECONDS,
        "PIP_TIMEOUT_SECONDS",
    )
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "--upgrade", "--user", "pip"],
        timeout=timeout_seconds,
    )
    subprocess.check_call(
        [python_cmd, "-m", "pip", "install", "--user", "-r", str(requirements)],
        timeout=timeout_seconds,
    )


def _install_requirements_with_fallback(
    requirements: Path,
    python_cmd: str,
    debug_mode: bool,
) -> tuple[bool, str]:
    _validate_requirements_path(requirements)
    interpreter = _validate_python_cmd(python_cmd)
    debug_enabled = _validate_debug_mode(debug_mode)

    try:
        _run_pip_install(requirements, interpreter)
        return True, "Standard-Installation erfolgreich."
    except (subprocess.SubprocessError, OSError) as exc:
        _print_warn(
            "Standard-Installation fehlgeschlagen. "
            "Starte Fallback ohne Admin-Rechte (--user)."
        )
        _print_debug(f"Fehler in Standard-Installation: {exc}", debug_enabled)

    try:
        _run_pip_install_user(requirements, interpreter)
        return True, "Fallback-Installation mit --user erfolgreich."
    except (subprocess.SubprocessError, OSError) as exc:
        return (
            False,
            "Automatische Installation fehlgeschlagen. "
            "Bitte Internet, Rechte und Requirements-Datei prüfen. "
            f"Letzter Fehler: {exc}",
        )


def _run_pip_install_packages(
    package_names: list[str], python_cmd: str
) -> None:
    if not isinstance(package_names, list):
        raise TypeError("package_names muss eine Liste sein.")
    cleaned_packages: list[str] = []
    for package_name in package_names:
        if not isinstance(package_name, str) or not package_name.strip():
            raise ValueError(
                "Jeder Paketname muss ein nicht-leerer String sein."
            )
        cleaned_packages.append(package_name.strip())

    interpreter = _validate_python_cmd(python_cmd)
    subprocess.check_call(
        [interpreter, "-m", "pip", "install", "--upgrade", *cleaned_packages],
        timeout=_validate_timeout_seconds(
            PIP_TIMEOUT_SECONDS,
            "PIP_TIMEOUT_SECONDS",
        ),
    )


def _module_import_ok(module_name: str, python_cmd: str) -> bool:
    return (
        subprocess.run(
            [python_cmd, "-c", f"import {module_name}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=_validate_timeout_seconds(
                IMPORT_TIMEOUT_SECONDS,
                "IMPORT_TIMEOUT_SECONDS",
            ),
        ).returncode
        == 0
    )


def _network_reachable(host: str, port: int, timeout_seconds: int) -> bool:
    if not isinstance(host, str) or not host.strip():
        raise ValueError("host muss ein nicht-leerer String sein.")
    if not isinstance(port, int):
        raise TypeError("port muss ein int sein.")
    if not (1 <= port <= 65535):
        raise ValueError("port muss zwischen 1 und 65535 liegen.")
    timeout_value = _validate_timeout_seconds(
        timeout_seconds,
        "timeout_seconds",
    )
    try:
        with socket.create_connection(
            (host.strip(), port), timeout=timeout_value
        ):
            return True
    except OSError:
        return False


def _attempt_tool_repair(
    failed_tools: list[str], python_cmd: str, debug_mode: bool
) -> list[str]:
    if not isinstance(failed_tools, list):
        raise TypeError("failed_tools muss eine Liste sein.")
    if not isinstance(debug_mode, bool):
        raise TypeError("debug_mode muss ein bool sein.")

    tools_to_repair = _validate_tool_names(failed_tools)
    if not tools_to_repair:
        return []

    _print_info(
        "Starte automatische Reparatur für fehlende Prüftools: "
        + ", ".join(tools_to_repair)
    )
    _print_debug(
        "Auto-Reparatur nutzt pip --upgrade auf fehlenden Tools.",
        debug_mode,
    )
    try:
        _run_pip_install_packages(tools_to_repair, python_cmd)
    except (TypeError, ValueError, subprocess.SubprocessError) as exc:
        _print_warn(
            "Automatische Reparatur konnte nicht vollständig ausgeführt "
            f"werden: {exc}"
        )
        return tools_to_repair

    unresolved_tools: list[str] = []
    for tool in tools_to_repair:
        module_name = TOOL_MODULES[tool]
        if _module_import_ok(module_name, python_cmd):
            _print_ok(f"Tool nach Reparatur bereit: {tool}")
        else:
            unresolved_tools.append(tool)
            _print_warn(f"Tool trotz Reparatur nicht importierbar: {tool}")

    return unresolved_tools


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
    if _network_reachable("pypi.org", 443, NETWORK_TIMEOUT_SECONDS):
        _print_ok("Netzwerk-Check: pypi.org erreichbar.")
    else:
        _print_warn(
            "Netzwerk-Check: pypi.org aktuell nicht erreichbar. "
            "Falls Installation fehlschlaegt, bitte Internet pruefen "
            "oder spaeter erneut starten."
        )
    _print_info(f"Starte QA-Preflight mit {interpreter}")
    _print_debug(
        f"Installiere Abhängigkeiten aus: {requirements}",
        debug_enabled,
    )
    install_ok, install_message = _install_requirements_with_fallback(
        requirements,
        interpreter,
        debug_enabled,
    )
    if install_ok:
        _print_ok(install_message)
    else:
        print("❌ Abhängigkeiten konnten nicht vollständig installiert werden.")
        print(f"💡 Ursache: {install_message}")
        print(
            "💡 Lösung: Internet, Rechte und Requirements-Datei prüfen; "
            f"Befehl manuell testen: {interpreter} -m pip install -r {requirements}"
        )
        print(
            "💡 Falls Rechte fehlen, probiere ohne Admin-Rechte: "
            f"{interpreter} -m pip install --user -r {requirements}"
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
        failed_tools = _attempt_tool_repair(
            failed_tools,
            interpreter,
            debug_enabled,
        )

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
