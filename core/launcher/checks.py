from __future__ import annotations

import shutil
import sys
from pathlib import Path

from .models import PackageManagerInfo
from .network import detect_linux_distribution


def format_command(command: list[str]) -> str:
    return " ".join(command)


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


def ffmpeg_install_hint() -> str:
    if not sys.platform.startswith("linux"):
        return "Bitte ffmpeg manuell installieren."
    manager = linux_package_manager()
    if not manager:
        return "Linux-Distribution nicht erkannt. Bitte ffmpeg manuell installieren."
    if manager.update_cmd:
        combined = (
            f"{format_command(manager.update_cmd)} && "
            f"{format_command(manager.install_cmd)}"
        )
    else:
        combined = format_command(manager.install_cmd)
    return f"Befehl ({manager.name}): {combined}"


def write_permissions_ok(target_dir: Path) -> bool:
    from tempfile import NamedTemporaryFile

    if not isinstance(target_dir, Path):
        raise TypeError("target_dir muss ein Path sein.")
    if not target_dir.exists() or not target_dir.is_dir():
        return False
    try:
        with NamedTemporaryFile(dir=target_dir, delete=True):
            return True
    except OSError:
        return False


def ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
