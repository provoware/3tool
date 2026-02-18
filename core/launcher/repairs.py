from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable

LOGGER = logging.getLogger("videobatch_launcher")
ENV_DIR_NAME = ".videotool_env"


def in_venv() -> bool:
    return (
        hasattr(sys, "real_prefix")
        or getattr(sys, "base_prefix", sys.prefix) != sys.prefix
        or bool(os.environ.get("VIRTUAL_ENV"))
    )


def env_dir(project_root: Path = Path.cwd()) -> Path:
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein.")
    return (project_root / ENV_DIR_NAME).resolve()


def ensure_venv(project_root: Path = Path.cwd()) -> None:
    target = env_dir(project_root)
    if not target.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(target)])


def install_missing_packages_with_retries(
    py: str,
    missing_packages: Iterable[str],
    *,
    pip_install,
    missing_runtime_packages,
    in_venv_check,
) -> tuple[bool, str]:
    packages = [pkg for pkg in missing_packages if isinstance(pkg, str) and pkg]
    if not packages:
        LOGGER.info("Keine fehlenden Pakete erkannt.")
        return True, "Alle Pakete vorhanden."

    try:
        pip_install(py, packages)
    except subprocess.SubprocessError as exc:
        if in_venv_check():
            LOGGER.error(
                "Installation in venv fehlgeschlagen; --user ist im venv deaktiviert: %s",
                exc,
            )
            return (
                False,
                "Installation in der virtuellen Umgebung fehlgeschlagen. "
                "Bitte zuerst pip/venv reparieren (python -m ensurepip --upgrade, "
                "danach venv neu erstellen) und erneut starten.",
            )
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
        return (
            False,
            "Installation lief, aber folgende Pakete fehlen weiter: "
            + ", ".join(unresolved),
        )
    return True, "Pakete installiert und erfolgreich geprüft: " + ", ".join(
        packages
    )
