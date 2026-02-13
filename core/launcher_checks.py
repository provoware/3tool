from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.dependency_consistency import RUNTIME_PACKAGES

REQ_PKGS = list(RUNTIME_PACKAGES)
PACKAGE_IMPORT_NAMES = {
    "PySide6": "PySide6",
    "Pillow": "PIL",
    "ffmpeg-python": "ffmpeg",
}
ENV_DIR = Path(".videotool_env").resolve()
MIN_PYTHON = (3, 8)

LOGGER = logging.getLogger("videobatch_launcher")


def configure_logging(log_file: Path, debug: bool = False) -> None:
    """Configure launcher logging to file and console output."""
    level = logging.DEBUG if debug else logging.INFO
    log_file.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.handlers.clear()
    LOGGER.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(stream_handler)


@dataclass(frozen=True)
class PackageManagerInfo:
    name: str
    update_cmd: list[str] | None
    install_cmd: list[str]


@dataclass(frozen=True)
class CheckResult:
    key: str
    title: str
    ok: bool
    detail: str
    fix_hint: str | None = None
    blocking: bool = True


@dataclass(frozen=True)
class RepairResult:
    key: str
    title: str
    ok: bool
    detail: str
    skipped_offline: bool = False


@dataclass(frozen=True)
class ReleaseReadinessResult:
    key: str
    title: str
    ok: bool
    detail: str
    recommendation: str
    blocking: bool = True


def in_venv() -> bool:
    return (
        hasattr(sys, "real_prefix")
        or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
        or bool(os.environ.get("VIRTUAL_ENV"))
    )


def venv_python() -> Path:
    """Return path to launcher venv or current interpreter if missing."""
    path = ENV_DIR / ("Scripts" if os.name == "nt" else "bin") / "python"
    return path if path.exists() else Path(sys.executable)


def ensure_venv() -> None:
    if not ENV_DIR.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(ENV_DIR)])


def pip_ok(py: str) -> bool:
    py = validated_python_command(py)
    return (
        subprocess.run(
            [py, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def pip_show(py: str, pkg: str) -> bool:
    py = validated_python_command(py)
    if not isinstance(pkg, str) or not pkg.strip():
        raise ValueError("pkg muss ein nicht-leerer String sein.")
    return (
        subprocess.run(
            [py, "-m", "pip", "show", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def module_import_ok(py: str, module_name: str) -> bool:
    py = validated_python_command(py)
    if not isinstance(module_name, str) or not module_name.strip():
        raise ValueError("module_name muss ein nicht-leerer String sein.")
    return (
        subprocess.run(
            [py, "-c", f"import {module_name}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def missing_runtime_packages(py: str) -> list[str]:
    py = validated_python_command(py)
    missing: list[str] = []
    for package_name in REQ_PKGS:
        import_name = PACKAGE_IMPORT_NAMES.get(package_name, package_name)
        if not pip_show(py, package_name) or not module_import_ok(
            py, import_name
        ):
            missing.append(package_name)
    return missing


def ensure_pip(py: str) -> bool:
    py = validated_python_command(py)
    if pip_ok(py):
        return True
    try:
        subprocess.check_call([py, "-m", "ensurepip", "--upgrade"])
        return pip_ok(py)
    except subprocess.SubprocessError as exc:
        LOGGER.warning("ensurepip failed: %s", exc)
        return False


def pip_install(py: str, pkgs: Iterable[str]) -> None:
    py = validated_python_command(py)
    packages = list(pkgs)
    if not packages:
        return
    subprocess.check_call(
        [py, "-m", "pip", "install", "--upgrade", "pip"],
        stdout=subprocess.DEVNULL,
    )
    subprocess.check_call([py, "-m", "pip", "install", "--upgrade"] + packages)


def install_missing_packages_with_retries(
    py: str, missing_packages: Iterable[str]
) -> tuple[bool, str]:
    """Install missing packages with a fallback strategy and clear feedback."""
    py = validated_python_command(py)
    packages = [pkg for pkg in missing_packages if isinstance(pkg, str) and pkg]
    if not packages:
        LOGGER.info("Keine fehlenden Pakete erkannt.")
        return True, "Alle Pakete vorhanden."

    try:
        pip_install(py, packages)
    except subprocess.SubprocessError as exc:
        LOGGER.warning(
            "Standard-Installation fehlgeschlagen, nutze Fallback mit --user: %s",
            exc,
        )
        try:
            subprocess.check_call(
                [py, "-m", "pip", "install", "--upgrade", "--user"] + packages
            )
        except subprocess.SubprocessError as fallback_exc:
            LOGGER.error(
                "Fallback-Installation fehlgeschlagen: %s", fallback_exc
            )
            return (
                False,
                "Pakete konnten nicht installiert werden. "
                "Bitte Internet, Rechte und den Befehl "
                f"'{py} -m pip install --upgrade {' '.join(packages)}' prüfen.",
            )

    unresolved = missing_runtime_packages(py)
    if unresolved:
        LOGGER.error(
            "Paket-Reparatur abgeschlossen, aber weiter fehlend: %s",
            ", ".join(unresolved),
        )
        return (
            False,
            "Installation lief, aber folgende Pakete fehlen weiter: "
            + ", ".join(unresolved),
        )

    LOGGER.info("Paket-Reparatur erfolgreich: %s", ", ".join(packages))
    return True, "Pakete installiert und erfolgreich geprüft: " + ", ".join(
        packages
    )


def has_internet(timeout: float = 2.0) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout)
    except OSError:
        return False
    return True


def parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"')
        data[key] = value
    return data


def detect_linux_distribution() -> dict[str, str]:
    data = parse_os_release()
    return {
        "id": data.get("ID", ""),
        "name": data.get("NAME", ""),
        "like": data.get("ID_LIKE", ""),
    }


def linux_package_manager() -> PackageManagerInfo | None:
    info = detect_linux_distribution()
    distro_id = info["id"].lower()
    distro_like = info["like"].lower().split()
    candidates = [distro_id] + distro_like
    if any(value in candidates for value in ["debian", "ubuntu"]):
        return PackageManagerInfo(
            name="apt (Paketmanager/Software-Verwalter)",
            update_cmd=["sudo", "apt", "update"],
            install_cmd=["sudo", "apt", "install", "-y", "ffmpeg"],
        )
    if "fedora" in candidates:
        return PackageManagerInfo(
            name="dnf (Paketmanager/Software-Verwalter)",
            update_cmd=None,
            install_cmd=["sudo", "dnf", "install", "-y", "ffmpeg"],
        )
    if "arch" in candidates:
        return PackageManagerInfo(
            name="pacman (Paketmanager/Software-Verwalter)",
            update_cmd=None,
            install_cmd=["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"],
        )
    if any(value in candidates for value in ["suse", "opensuse"]):
        return PackageManagerInfo(
            name="zypper (Paketmanager/Software-Verwalter)",
            update_cmd=None,
            install_cmd=["sudo", "zypper", "install", "-y", "ffmpeg"],
        )
    return None


def format_command(command: list[str]) -> str:
    return " ".join(command)


def validated_python_command(py: str) -> str:
    if not isinstance(py, str) or not py.strip():
        raise ValueError("py muss ein nicht-leerer String sein.")
    return py


def ffmpeg_install_hint() -> str:
    if not sys.platform.startswith("linux"):
        return "Bitte ffmpeg manuell installieren."
    manager = linux_package_manager()
    if not manager:
        return (
            "Linux-Distribution nicht erkannt. Bitte ffmpeg manuell "
            "installieren."
        )
    if manager.update_cmd:
        combined = (
            f"{format_command(manager.update_cmd)} && "
            f"{format_command(manager.install_cmd)}"
        )
    else:
        combined = format_command(manager.install_cmd)
    return f"Befehl ({manager.name}): {combined}"


def write_permissions_ok(target_dir: Path) -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=target_dir, delete=True):
            return True
    except OSError:
        return False


def check_python_version() -> CheckResult:
    current = sys.version_info[:3]
    ok = current >= MIN_PYTHON
    detail = f"Gefunden: {current[0]}.{current[1]}.{current[2]}"
    hint = (
        "Bitte installiere eine neuere Python-Version (mindestens "
        f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]})."
    )
    return CheckResult(
        key="python_version",
        title="Python-Version",
        ok=ok,
        detail=detail if ok else f"{detail}. {hint}",
        fix_hint="https://www.python.org/downloads/" if not ok else None,
    )


def check_venv() -> CheckResult:
    ok = ENV_DIR.exists()
    detail = (
        "Virtuelle Umgebung vorhanden." if ok else "Virtuelle Umgebung fehlt."
    )
    hint = "Befehl: python3 -m venv .videotool_env"
    return CheckResult(
        key="venv",
        title="Virtuelle Umgebung (venv)",
        ok=ok,
        detail=detail,
        fix_hint=None if ok else hint,
    )


def check_pip(py: str) -> CheckResult:
    ok = pip_ok(py)
    detail = "pip ist bereit." if ok else "pip fehlt oder ist defekt."
    hint = "Befehl: python3 -m ensurepip --upgrade"
    return CheckResult(
        key="pip",
        title="pip (Paket-Manager)",
        ok=ok,
        detail=detail,
        fix_hint=None if ok else hint,
    )


def check_packages(py: str) -> CheckResult:
    missing = missing_runtime_packages(py)
    ok = not missing
    detail = (
        "Alle benötigten Python-Pakete sind installiert."
        if ok
        else f"Fehlend: {', '.join(missing)}"
    )
    hint = (
        f"Befehl: {py} -m pip install --upgrade " + " ".join(missing)
        if missing
        else None
    )
    return CheckResult(
        key="packages",
        title="Python-Pakete (PySide6, Pillow, ffmpeg-python)",
        ok=ok,
        detail=detail,
        fix_hint=hint,
    )


def check_ffmpeg() -> CheckResult:
    ok = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    detail = "ffmpeg und ffprobe gefunden." if ok else "ffmpeg/ffprobe fehlen."
    hint = ffmpeg_install_hint()
    return CheckResult(
        key="ffmpeg",
        title="ffmpeg/ffprobe (Video-Werkzeuge)",
        ok=ok,
        detail=detail,
        fix_hint=None if ok else hint,
    )


def check_write_permissions(target_dir: Path) -> CheckResult:
    ok = write_permissions_ok(target_dir)
    detail = (
        "Schreibrechte vorhanden."
        if ok
        else "Keine Schreibrechte im Projektordner."
    )
    hint = "Befehl: chmod -R u+rw <projektordner>"
    return CheckResult(
        key="write_permissions",
        title="Schreibrechte (Projektordner)",
        ok=ok,
        detail=detail,
        fix_hint=None if ok else hint,
    )


def check_internet() -> CheckResult:
    ok = has_internet()
    detail = (
        "Internetverbindung vorhanden." if ok else "Kein Internet erreichbar."
    )
    return CheckResult(
        key="internet",
        title="Internet (für Downloads)",
        ok=ok,
        detail=detail,
        blocking=False,
    )


def collect_checks(py: str, target_dir: Path) -> list[CheckResult]:
    py = validated_python_command(py)
    if not isinstance(target_dir, Path):
        raise TypeError("target_dir muss ein Path sein.")
    return [
        check_python_version(),
        check_venv(),
        check_pip(py),
        check_packages(py),
        check_ffmpeg(),
        check_write_permissions(target_dir),
        check_internet(),
    ]


def unresolved_todo_items(todo_file: Path) -> list[str]:
    if not isinstance(todo_file, Path):
        raise TypeError("todo_file muss ein Path sein.")
    if not todo_file.exists():
        return []
    unresolved: list[str] = []
    for line in todo_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            unresolved.append(stripped.removeprefix("- [ ]").strip())
    return unresolved


def evaluate_release_readiness(
    project_root: Path,
) -> list[ReleaseReadinessResult]:
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein.")

    checks: list[ReleaseReadinessResult] = []
    todo_file = project_root / "todo.txt"
    open_items = unresolved_todo_items(todo_file)
    checks.append(
        ReleaseReadinessResult(
            key="todo",
            title="Offene Aufgaben (todo.txt)",
            ok=not open_items,
            detail=(
                "Keine offenen Aufgaben gefunden."
                if not open_items
                else f"Noch offen: {', '.join(open_items[:3])}"
            ),
            recommendation=(
                "Release-Kandidat: Aufgabenliste ist abgeschlossen."
                if not open_items
                else "Bitte offene Aufgaben abschließen und abhaken."
            ),
        )
    )

    must_exist = {
        "quality_script": (
            project_root / "scripts" / "quality_check.sh",
            "Qualitäts-Check-Skript",
            "Datei prüfen und Check-Befehl dokumentieren.",
        ),
        "tests": (
            project_root / "tests",
            "Automatische Tests",
            "Mindestens Smoke- und Start-Tests ergänzen.",
        ),
        "changelog": (
            project_root / "CHANGELOG.md",
            "Changelog für Release",
            "Änderungen vor Release im Changelog beschreiben.",
        ),
    }
    for key, (path, title, recommendation) in must_exist.items():
        exists = path.exists()
        checks.append(
            ReleaseReadinessResult(
                key=key,
                title=title,
                ok=exists,
                detail=(f"Gefunden: {path}" if exists else f"Fehlt: {path}"),
                recommendation=("OK" if exists else recommendation),
            )
        )

    return checks


def run_repairs(py: str, target_dir: Path) -> list[RepairResult]:
    py = validated_python_command(py)
    if not isinstance(target_dir, Path):
        raise TypeError("target_dir muss ein Path sein.")
    results: list[RepairResult] = []
    online = has_internet()

    try:
        ensure_venv()
        results.append(
            RepairResult(
                "venv", "Virtuelle Umgebung (venv)", True, "Venv ist bereit."
            )
        )
    except subprocess.SubprocessError as exc:
        results.append(
            RepairResult(
                "venv",
                "Virtuelle Umgebung (venv)",
                False,
                f"Venv konnte nicht erstellt werden: {exc}",
            )
        )

    pip_ready = ensure_pip(py)
    results.append(
        RepairResult(
            "pip",
            "pip (Paket-Manager)",
            pip_ready,
            (
                "pip ist bereit."
                if pip_ready
                else "pip konnte nicht aktiviert werden."
            ),
        )
    )

    if online:
        missing = missing_runtime_packages(py)
        if missing and pip_ready:
            package_ok, package_detail = install_missing_packages_with_retries(
                py, missing
            )
            results.append(
                RepairResult(
                    "packages",
                    "Python-Pakete",
                    package_ok,
                    package_detail,
                )
            )
        else:
            results.append(
                RepairResult(
                    "packages",
                    "Python-Pakete",
                    True,
                    "Alle Pakete vorhanden.",
                )
            )
    else:
        results.append(
            RepairResult(
                "packages",
                "Python-Pakete",
                False,
                "Kein Internet, Installation übersprungen.",
                skipped_offline=True,
            )
        )

    ffmpeg_ok = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    if ffmpeg_ok:
        results.append(
            RepairResult(
                "ffmpeg",
                "ffmpeg/ffprobe",
                True,
                "ffmpeg/ffprobe sind vorhanden.",
            )
        )
    elif not online:
        results.append(
            RepairResult(
                "ffmpeg",
                "ffmpeg/ffprobe",
                False,
                "Kein Internet, Installation übersprungen.",
                skipped_offline=True,
            )
        )
    elif sys.platform.startswith("linux"):
        manager = linux_package_manager()
        if not manager:
            results.append(
                RepairResult(
                    "ffmpeg",
                    "ffmpeg/ffprobe",
                    False,
                    (
                        "Linux-Distribution nicht erkannt. Bitte ffmpeg "
                        "manuell installieren."
                    ),
                )
            )
        else:
            try:
                if manager.update_cmd:
                    subprocess.check_call(manager.update_cmd)
                subprocess.check_call(manager.install_cmd)
                ffmpeg_ok = bool(
                    shutil.which("ffmpeg") and shutil.which("ffprobe")
                )
                results.append(
                    RepairResult(
                        "ffmpeg",
                        "ffmpeg/ffprobe",
                        ffmpeg_ok,
                        (
                            "ffmpeg installiert."
                            if ffmpeg_ok
                            else "ffmpeg Installation fehlte."
                        ),
                    )
                )
            except subprocess.SubprocessError as exc:
                results.append(
                    RepairResult(
                        "ffmpeg",
                        "ffmpeg/ffprobe",
                        False,
                        f"ffmpeg Installation fehlgeschlagen: {exc}",
                    )
                )
    else:
        results.append(
            RepairResult(
                "ffmpeg",
                "ffmpeg/ffprobe",
                False,
                "Bitte ffmpeg manuell installieren.",
            )
        )

    writable = write_permissions_ok(target_dir)
    results.append(
        RepairResult(
            "write_permissions",
            "Schreibrechte (Projektordner)",
            writable,
            (
                "Schreibrechte vorhanden."
                if writable
                else "Bitte Schreibrechte prüfen."
            ),
        )
    )

    return results


def beginner_recovery_hints(results: Iterable[RepairResult]) -> list[str]:
    result_list = list(results)
    hints: list[str] = []
    failed = {item.key for item in result_list if not item.ok}
    if "pip" in failed or "packages" in failed:
        hints.append(
            "Python-Pakete konnten nicht vollstaendig installiert werden. "
            "Bitte Internet, Rechte und danach den Button 'Reparieren' "
            "noch einmal pruefen."
        )
    if "ffmpeg" in failed:
        hints.append(
            "Video-Werkzeuge fehlen noch. Nutzen Sie den angezeigten "
            "Befehl fuer Ihr System (Paketmanager = Software-Verwalter)."
        )
    if "write_permissions" in failed:
        hints.append(
            "Es fehlen Schreibrechte im Projektordner. Starten Sie das Tool "
            "in einem eigenen Benutzerordner oder passen Sie Rechte an."
        )
    if any(item.skipped_offline for item in result_list):
        hints.append(
            "Offline erkannt: Nach Verbindungsaufbau bitte Reparatur erneut "
            "starten, damit fehlende Pakete automatisch nachinstalliert "
            "werden."
        )
    return hints
