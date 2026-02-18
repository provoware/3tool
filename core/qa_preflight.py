from __future__ import annotations

import argparse
import json
import shlex
import socket
import shutil
import subprocess
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from core.user_feedback import print_debug, print_feedback

TOOL_MODULES: Final[dict[str, str]] = {
    "black": "black",
    "ruff": "ruff",
    "mypy": "mypy",
    "pytest": "pytest",
    "flake8": "flake8",
    "isort": "isort",
    "autoflake": "autoflake",
}
DEFAULT_QA_TOOLS: Final[list[str]] = [
    "ruff",
    "black",
    "mypy",
    "pytest",
    "flake8",
    "isort",
    "autoflake",
]
TOOL_PROFILES: Final[dict[str, list[str]]] = {
    "standard": DEFAULT_QA_TOOLS,
    "quick": ["ruff", "black", "pytest"],
    "strict": [
        "ruff",
        "black",
        "mypy",
        "pytest",
        "flake8",
        "isort",
        "autoflake",
    ],
}

PIP_TIMEOUT_SECONDS: Final[int] = 300
IMPORT_TIMEOUT_SECONDS: Final[int] = 20
NETWORK_TIMEOUT_SECONDS: Final[int] = 3
NETWORK_ENDPOINTS: Final[tuple[tuple[str, int], ...]] = (
    ("pypi.org", 443),
    ("files.pythonhosted.org", 443),
)


def _validate_requirements_path(path: Path) -> None:
    if not isinstance(path, Path):
        raise TypeError("path muss ein Path sein.")
    if not path.exists() or not path.is_file():
        raise ValueError(f"Requirements-Datei fehlt: {path}")


def _validate_tool_names(tool_names: list[str]) -> list[str]:
    if not isinstance(tool_names, list):
        raise TypeError("tool_names muss eine Liste sein.")
    cleaned: list[str] = []
    seen: set[str] = set()
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
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(normalized)

    if not cleaned:
        raise ValueError("Mindestens ein Tool-Name ist erforderlich.")

    return cleaned


def _validate_python_cmd(python_cmd: str) -> str:
    if not isinstance(python_cmd, str):
        raise TypeError("python_cmd muss ein String sein.")
    interpreter = python_cmd.strip()
    if not interpreter:
        raise ValueError("python_cmd muss ein nicht-leerer String sein.")
    return interpreter


def _python_not_found_help(interpreter: str) -> list[str]:
    validated_interpreter = _validate_python_cmd(interpreter)
    quoted_interpreter = shlex.quote(validated_interpreter)
    return [
        "Python installieren oder korrekten Interpreterpfad mit --python setzen.",
        "Schnelltest im Terminal:",
        f"- {quoted_interpreter} --version",
        f"- which {quoted_interpreter}",
    ]


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


def _validate_report_path(report_path: Path | None) -> Path | None:
    if report_path is None:
        return None
    if not isinstance(report_path, Path):
        raise TypeError("report_path muss ein Path oder None sein.")
    if report_path.exists() and report_path.is_dir():
        raise ValueError("report_path darf kein Verzeichnis sein.")
    return report_path


def _validate_validate_only(validate_only: bool) -> bool:
    if not isinstance(validate_only, bool):
        raise TypeError("validate_only muss ein bool sein.")
    return validate_only


def _resolve_cli_tools(profile: str, cli_tools: list[str] | None) -> list[str]:
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("profile muss ein nicht-leerer String sein.")
    normalized_profile = profile.strip().lower()
    if normalized_profile not in TOOL_PROFILES:
        allowed_profiles = ", ".join(sorted(TOOL_PROFILES))
        raise ValueError(
            f"Unbekanntes Profil '{normalized_profile}'. Erlaubt: {allowed_profiles}"
        )

    if cli_tools is None:
        return _validate_tool_names(list(TOOL_PROFILES[normalized_profile]))

    return _validate_tool_names(cli_tools)


def _validate_package_names(package_names: list[str]) -> list[str]:
    if not isinstance(package_names, list):
        raise TypeError("package_names muss eine Liste sein.")

    cleaned_packages: list[str] = []
    seen: set[str] = set()
    for package_name in package_names:
        if not isinstance(package_name, str) or not package_name.strip():
            raise ValueError(
                "Jeder Paketname muss ein nicht-leerer String sein."
            )
        normalized = package_name.strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_packages.append(normalized)

    if not cleaned_packages:
        raise ValueError("Mindestens ein Paketname ist erforderlich.")

    return cleaned_packages


def _manual_recovery_commands(
    python_cmd: str, requirements: Path, failed_tools: list[str]
) -> list[str]:
    interpreter = _validate_python_cmd(python_cmd)
    _validate_requirements_path(requirements)
    valid_tools = _validate_tool_names(failed_tools)

    quoted_interpreter = shlex.quote(interpreter)
    quoted_requirements = shlex.quote(str(requirements))
    command_list = [
        f"{quoted_interpreter} -m pip install --upgrade pip",
        (f"{quoted_interpreter} -m pip install -r " f"{quoted_requirements}"),
        (
            f"{quoted_interpreter} -m pip install --user -r "
            f"{quoted_requirements}"
        ),
    ]
    if valid_tools:
        quoted_tools = " ".join(shlex.quote(tool) for tool in valid_tools)
        command_list.append(
            f"{quoted_interpreter} -m pip install --upgrade {quoted_tools}"
        )

    return command_list


def _write_preflight_report(
    report_path: Path | None,
    report_data: dict[str, object],
) -> None:
    target_path = _validate_report_path(report_path)
    if target_path is None:
        return
    if not isinstance(report_data, dict):
        raise TypeError("report_data muss ein Dictionary sein.")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(report_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _novice_recovery_steps(
    title: str,
    python_cmd: str,
    requirements: Path,
    failed_tools: list[str],
) -> list[str]:
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title muss ein nicht-leerer String sein.")

    interpreter = _validate_python_cmd(python_cmd)
    _validate_requirements_path(requirements)
    valid_tools = _validate_tool_names(failed_tools)
    commands = _manual_recovery_commands(
        interpreter,
        requirements,
        valid_tools,
    )

    quoted_interpreter = shlex.quote(interpreter)
    return [
        title.strip(),
        "1) Interpreter (Python-Starter) testen:",
        f"   - {quoted_interpreter} --version",
        "2) Paketverwaltung (pip = Installationswerkzeug) testen:",
        f"   - {quoted_interpreter} -m pip --version",
        "3) Abhaengigkeiten neu installieren:",
        f"   - {commands[1]}",
        "4) Falls Rechte fehlen, ohne Adminrechte wiederholen:",
        f"   - {commands[2]}",
        "5) Fehlende QA-Tools gezielt reparieren:",
        f"   - {commands[3]}",
    ]


def _print_novice_recovery_steps(
    python_cmd: str,
    requirements: Path,
    failed_tools: list[str],
) -> list[str]:
    steps = _novice_recovery_steps(
        "Bitte nacheinander ausführen:",
        python_cmd,
        requirements,
        failed_tools,
    )
    print("💡 Lösungsvorschläge (Kopieren + Einfügen):")
    for step in steps:
        print(step)
    return steps


def _run_checked_call(command: list[str], timeout_seconds: int) -> None:
    validated_command = _validate_command(command)

    subprocess.check_call(
        validated_command,
        timeout=_validate_timeout_seconds(timeout_seconds, "timeout_seconds"),
    )


def _run_quiet(command: list[str], timeout_seconds: int) -> bool:
    validated_command = _validate_command(command)

    try:
        return (
            subprocess.run(
                validated_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=_validate_timeout_seconds(
                    timeout_seconds, "timeout_seconds"
                ),
            ).returncode
            == 0
        )
    except (subprocess.SubprocessError, OSError):
        return False


def _validate_command(command: list[str]) -> list[str]:
    if not isinstance(command, list) or not command:
        raise ValueError("command muss eine nicht-leere Liste sein.")
    validated_parts: list[str] = []
    for part in command:
        if not isinstance(part, str) or not part.strip():
            raise ValueError(
                "Jeder Kommando-Teil muss ein nicht-leerer String sein."
            )
        validated_parts.append(part.strip())
    return validated_parts


def _build_error_help(exc: BaseException) -> str:
    if not isinstance(exc, BaseException):
        raise TypeError("exc muss eine Exception sein.")
    return (
        f"{exc.__class__.__name__}: {exc}. "
        "Bitte Debug-Modus (--debug) nutzen und den letzten Schritt erneut "
        "ausführen."
    )


def _run_pip_install(requirements: Path, python_cmd: str) -> None:
    timeout_seconds = _validate_timeout_seconds(
        PIP_TIMEOUT_SECONDS,
        "PIP_TIMEOUT_SECONDS",
    )
    _run_checked_call(
        [python_cmd, "-m", "pip", "install", "--upgrade", "pip"],
        timeout_seconds,
    )
    _run_checked_call(
        [python_cmd, "-m", "pip", "install", "-r", str(requirements)],
        timeout_seconds,
    )


def _run_pip_install_user(requirements: Path, python_cmd: str) -> None:
    timeout_seconds = _validate_timeout_seconds(
        PIP_TIMEOUT_SECONDS,
        "PIP_TIMEOUT_SECONDS",
    )
    _run_checked_call(
        [python_cmd, "-m", "pip", "install", "--upgrade", "--user", "pip"],
        timeout_seconds,
    )
    _run_checked_call(
        [python_cmd, "-m", "pip", "install", "--user", "-r", str(requirements)],
        timeout_seconds,
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
        print_feedback(
            "warn",
            "Standard-Installation fehlgeschlagen. "
            "Starte Fallback ohne Admin-Rechte (--user).",
        )
        print_debug(f"Fehler in Standard-Installation: {exc}", debug_enabled)

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
    cleaned_packages = _validate_package_names(package_names)
    interpreter = _validate_python_cmd(python_cmd)
    _run_checked_call(
        [interpreter, "-m", "pip", "install", "--upgrade", *cleaned_packages],
        _validate_timeout_seconds(
            PIP_TIMEOUT_SECONDS,
            "PIP_TIMEOUT_SECONDS",
        ),
    )


def _module_import_ok(module_name: str, python_cmd: str) -> bool:
    if not isinstance(module_name, str) or not module_name.strip():
        raise ValueError("module_name muss ein nicht-leerer String sein.")

    return _run_quiet(
        [python_cmd, "-c", f"import {module_name.strip()}"],
        _validate_timeout_seconds(
            IMPORT_TIMEOUT_SECONDS,
            "IMPORT_TIMEOUT_SECONDS",
        ),
    )


def _pip_available(python_cmd: str) -> bool:
    interpreter = _validate_python_cmd(python_cmd)
    return _run_quiet(
        [interpreter, "-m", "pip", "--version"],
        _validate_timeout_seconds(
            IMPORT_TIMEOUT_SECONDS,
            "IMPORT_TIMEOUT_SECONDS",
        ),
    )


def _ensure_pip_with_fallback(
    python_cmd: str, debug_mode: bool
) -> tuple[bool, str]:
    interpreter = _validate_python_cmd(python_cmd)
    debug_enabled = _validate_debug_mode(debug_mode)

    if _pip_available(interpreter):
        return True, "pip ist bereit."

    print_feedback(
        "warn",
        "pip ist aktuell nicht verfuegbar. Starte automatische Selbstreparatur "
        "mit ensurepip.",
    )
    print_debug(
        "Führe ensurepip --upgrade aus, um pip wiederherzustellen.",
        debug_enabled,
    )

    try:
        _run_checked_call(
            [interpreter, "-m", "ensurepip", "--upgrade"],
            _validate_timeout_seconds(
                PIP_TIMEOUT_SECONDS,
                "PIP_TIMEOUT_SECONDS",
            ),
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return (
            False,
            "pip-Selbstreparatur mit ensurepip fehlgeschlagen. "
            f"Details: {exc}",
        )

    if _pip_available(interpreter):
        return True, "pip wurde automatisch repariert (ensurepip)."

    return (
        False,
        "pip bleibt nach ensurepip nicht nutzbar. "
        "Bitte Python-Installation pruefen.",
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


def _network_any_reachable(
    endpoints: tuple[tuple[str, int], ...],
    timeout_seconds: int,
) -> tuple[bool, str]:
    if not isinstance(endpoints, tuple) or not endpoints:
        raise ValueError("endpoints muss ein nicht-leeres Tuple sein.")

    timeout_value = _validate_timeout_seconds(
        timeout_seconds,
        "timeout_seconds",
    )

    for endpoint in endpoints:
        if not isinstance(endpoint, tuple) or len(endpoint) != 2:
            raise ValueError(
                "Jeder Endpoint muss ein Tuple aus host und port sein."
            )
        host, port = endpoint
        if _network_reachable(host, port, timeout_value):
            return True, f"{host}:{port}"

    checked_hosts = ", ".join(f"{host}:{port}" for host, port in endpoints)
    return False, checked_hosts


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

    print_feedback(
        "info",
        "Starte automatische Reparatur für fehlende Prüftools: "
        + ", ".join(tools_to_repair),
    )
    print_debug(
        "Auto-Reparatur nutzt pip --upgrade auf fehlenden Tools.",
        debug_mode,
    )
    try:
        _run_pip_install_packages(tools_to_repair, python_cmd)
    except (TypeError, ValueError, subprocess.SubprocessError, OSError) as exc:
        print_feedback(
            "warn",
            "Automatische Reparatur konnte nicht vollständig ausgeführt "
            f"werden: {exc}",
        )
        return tools_to_repair

    unresolved_tools: list[str] = []
    for tool in tools_to_repair:
        module_name = TOOL_MODULES[tool]
        if _module_import_ok(module_name, python_cmd):
            print_feedback("ok", f"Tool nach Reparatur bereit: {tool}")
        else:
            unresolved_tools.append(tool)
            print_feedback(
                "warn", f"Tool trotz Reparatur nicht importierbar: {tool}"
            )

    return unresolved_tools


def _can_skip_install_when_offline(
    selected_tools: list[str], python_cmd: str, debug_mode: bool
) -> bool:
    tools = _validate_tool_names(selected_tools)
    interpreter = _validate_python_cmd(python_cmd)
    debug_enabled = _validate_debug_mode(debug_mode)

    if not tools:
        return False

    missing_tools: list[str] = []
    for tool in tools:
        module_name = TOOL_MODULES[tool]
        if not _module_import_ok(module_name, interpreter):
            missing_tools.append(tool)

    if missing_tools:
        print_debug(
            "Offline-Weiterlauf nicht möglich. Fehlende Tools: "
            + ", ".join(missing_tools),
            debug_enabled,
        )
        return False

    print_feedback(
        "ok",
        "Offline erkannt, aber alle Prüftools sind bereits verfügbar. "
        "Installation wird übersprungen.",
    )
    return True


def run_preflight(
    requirements: Path,
    tool_names: list[str],
    python_cmd: str,
    debug_mode: bool = False,
    report_path: Path | None = None,
    validate_only: bool = False,
) -> int:
    _validate_requirements_path(requirements)
    selected_tools = _validate_tool_names(tool_names)
    interpreter = _validate_python_cmd(python_cmd)
    debug_enabled = _validate_debug_mode(debug_mode)
    report_target = _validate_report_path(report_path)
    validation_only = _validate_validate_only(validate_only)
    started_at = datetime.now(UTC).isoformat()
    report: dict[str, object] = {
        "started_at_utc": started_at,
        "requirements": str(requirements),
        "python_cmd": interpreter,
        "debug_mode": debug_enabled,
        "selected_tools": selected_tools,
        "checks": [],
        "result": "failed",
        "help": [],
    }

    def _push_check(name: str, status: str, detail: str) -> None:
        checks = report["checks"]
        if not isinstance(checks, list):
            raise TypeError("report['checks'] muss eine Liste sein.")
        checks.append(
            {
                "name": name,
                "status": status,
                "detail": detail,
            }
        )

    print_feedback("ok", f"Requirements-Datei gefunden: {requirements}")
    print_feedback("info", f"Validierte Prüftools: {', '.join(selected_tools)}")
    if validation_only:
        print_feedback(
            "info",
            "Validierungsmodus aktiv: Es werden keine Pakete installiert oder repariert.",
        )
    print_debug(
        f"Debug-Modus aktiv. Interpreter-Kandidat: {interpreter}",
        debug_enabled,
    )

    if shutil.which(interpreter) is None:
        print(f"❌ Python-Interpreter nicht gefunden: {interpreter}")
        print("💡 Bitte Python installieren oder den Interpreterpfad prüfen.")
        print("💡 Schnelltest-Befehle:")
        for step in _python_not_found_help(interpreter)[2:]:
            print(step)
        _push_check("python", "error", f"Interpreter fehlt: {interpreter}")
        report["help"] = _python_not_found_help(interpreter)
        _write_preflight_report(report_target, report)
        return 1

    print_feedback("ok", f"Python-Interpreter gefunden: {interpreter}")
    _push_check("python", "ok", f"Interpreter gefunden: {interpreter}")

    pip_ok, pip_message = _ensure_pip_with_fallback(
        interpreter,
        debug_enabled,
    )
    if pip_ok:
        print_feedback("ok", pip_message)
        _push_check("pip", "ok", pip_message)
    else:
        print("❌ pip konnte nicht automatisch vorbereitet werden.")
        print(f"💡 Ursache: {pip_message}")
        print(
            "💡 Lösung: Python mit pip-Unterstützung installieren oder manuell "
            f"testen: {interpreter} -m ensurepip --upgrade"
        )
        _push_check("pip", "error", pip_message)
        report["help"] = [
            (
                "Python mit pip-Unterstützung installieren oder ensurepip "
                "manuell ausführen."
            )
        ]
        _write_preflight_report(report_target, report)
        return 1

    try:
        network_ok, network_detail = _network_any_reachable(
            NETWORK_ENDPOINTS,
            NETWORK_TIMEOUT_SECONDS,
        )
    except (TypeError, ValueError, OSError) as exc:
        detail = _build_error_help(exc)
        print_feedback(
            "warn",
            "Netzwerk-Check konnte nicht sicher ausgeführt werden. "
            "Es wird mit Installationsversuch fortgefahren.",
        )
        print_debug(f"Netzwerk-Check Fehlerdetail: {detail}", debug_enabled)
        network_ok = False
        network_detail = "Prüfung fehlgeschlagen"
        _push_check("network", "warn", detail)

    if network_ok:
        print_feedback(
            "ok", f"Netzwerk-Check: erreichbar über {network_detail}."
        )
        _push_check("network", "ok", f"Erreichbar: {network_detail}")
    else:
        print_feedback(
            "warn",
            f"Netzwerk-Check: Ziele nicht erreichbar ({network_detail}). "
            "Falls Installation fehlschlaegt, bitte Internet pruefen "
            "oder spaeter erneut starten.",
        )
        _push_check(
            "network",
            "warn",
            "Nicht erreichbar: " + network_detail,
        )
    print_feedback("info", f"Starte QA-Preflight mit {interpreter}")
    if validation_only:
        install_ok = True
        install_message = (
            "Installationsschritt bewusst übersprungen (--validate-only)."
        )
    else:
        if not network_ok and _can_skip_install_when_offline(
            selected_tools,
            interpreter,
            debug_enabled,
        ):
            print_feedback(
                "ok",
                "QA-Preflight erfolgreich ohne Neuinstallation (Offline-Modus).",
            )
            _push_check(
                "requirements_install",
                "ok",
                "Offline-Skip: Tools bereits verfügbar.",
            )
            report["result"] = "success"
            report["finished_at_utc"] = datetime.now(UTC).isoformat()
            _write_preflight_report(report_target, report)
            return 0

        print_debug(
            f"Installiere Abhängigkeiten aus: {requirements}",
            debug_enabled,
        )
        install_ok, install_message = _install_requirements_with_fallback(
            requirements,
            interpreter,
            debug_enabled,
        )
    if install_ok:
        install_status = "warn" if validation_only else "ok"
        print_feedback("ok" if not validation_only else "warn", install_message)
        _push_check("requirements_install", install_status, install_message)
    else:
        print("❌ Abhängigkeiten konnten nicht vollständig installiert werden.")
        print(f"💡 Ursache: {install_message}")
        help_steps = _print_novice_recovery_steps(
            interpreter,
            requirements,
            selected_tools,
        )
        _push_check("requirements_install", "error", install_message)
        report["help"] = help_steps
        report["finished_at_utc"] = datetime.now(UTC).isoformat()
        _write_preflight_report(report_target, report)
        return 1

    failed_tools: list[str] = []
    for tool in selected_tools:
        module_name = TOOL_MODULES[tool]
        print_debug(
            f"Prüfe Tool-Import: {tool} (Modul: {module_name})",
            debug_enabled,
        )
        tool_check_logged = False
        try:
            tool_ready = _module_import_ok(module_name, interpreter)
        except (
            TypeError,
            ValueError,
            OSError,
            subprocess.SubprocessError,
        ) as exc:
            tool_ready = False
            detail = _build_error_help(exc)
            print_feedback(
                "warn",
                f"Tool-Prüfung konnte nicht abgeschlossen werden: {tool}",
            )
            print_debug(
                f"Tool-Prüfung Fehlerdetail ({tool}): {detail}",
                debug_enabled,
            )
            _push_check(f"tool:{tool}", "warn", detail)
            tool_check_logged = True

        if tool_ready:
            print_feedback("ok", f"Tool bereit: {tool}")
            _push_check(f"tool:{tool}", "ok", "Import erfolgreich")
        elif tool not in failed_tools:
            failed_tools.append(tool)
            print_feedback("warn", f"Tool nicht importierbar: {tool}")
            if not tool_check_logged:
                _push_check(
                    f"tool:{tool}",
                    "warn",
                    "Import fehlgeschlagen",
                )

    if failed_tools and not validation_only:
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
        report["help"] = _print_novice_recovery_steps(
            interpreter,
            requirements,
            failed_tools,
        )
        report["finished_at_utc"] = datetime.now(UTC).isoformat()
        _write_preflight_report(report_target, report)
        return 1

    print_feedback(
        "ok",
        "QA-Preflight erfolgreich: alle benötigten Prüftools sind nutzbar.",
    )
    report["result"] = "success"
    report["finished_at_utc"] = datetime.now(UTC).isoformat()
    _write_preflight_report(report_target, report)
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
        default=None,
        help="Zu validierende Prüftools.",
    )
    parser.add_argument(
        "--profile",
        default="standard",
        choices=sorted(TOOL_PROFILES),
        help=(
            "Tool-Profil für typische Szenarien: "
            "quick (schnell), standard (Standard), strict (streng)."
        ),
    )
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Zeigt unterstützte Tools und Profile an und beendet das Programm.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Prüft nur, ob Tools verfügbar sind (keine Installation/Reparatur). "
            "Ideal für reine Statuskontrolle."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help=(
            "Aktiviert detaillierte Fehlersuche (Debug-Modus) mit "
            "zusätzlichen Zwischenschritten für die Fehlersuche."
        ),
    )
    parser.add_argument(
        "--report-json",
        default="",
        help=(
            "Optionaler Pfad für einen JSON-Statusbericht "
            "(maschinenlesbares Ergebnisprotokoll)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.list_tools:
            print("Unterstützte QA-Tools:")
            for tool_name in sorted(TOOL_MODULES):
                print(f"- {tool_name}")
            print("\nProfile:")
            for profile_name, tools in TOOL_PROFILES.items():
                print(f"- {profile_name}: {', '.join(tools)}")
            print(
                "\nTipp: --profile quick für schnellen Check oder "
                "--validate-only für reine Prüfung ohne Installation."
            )
            return 0

        selected_tools = _resolve_cli_tools(args.profile, args.tools)
        return run_preflight(
            Path(args.requirements),
            selected_tools,
            args.python,
            debug_mode=args.debug,
            report_path=Path(args.report_json) if args.report_json else None,
            validate_only=args.validate_only,
        )
    except (TypeError, ValueError) as exc:
        print(f"❌ Ungültige QA-Preflight-Eingabe: {exc}")
        print(
            "💡 Lösung: Dateipfade und Tool-Namen prüfen, "
            "z. B. --requirements requirements-dev.txt --tools ruff black"
        )
        return 1
    except Exception as exc:  # pragma: no cover - letzte Schutzschicht
        print("❌ Unerwarteter Fehler im QA-Preflight.")
        print(f"💡 Ursache: {_build_error_help(exc)}")
        if "--debug" in sys.argv:
            print_feedback("debug", traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
