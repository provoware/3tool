from __future__ import annotations

import logging
import socket
import urllib.error
import urllib.request
from http import HTTPStatus
from pathlib import Path

LOGGER = logging.getLogger("videobatch_launcher")


def dns_reachable(timeout: float) -> bool:
    if not isinstance(timeout, (int, float)):
        raise TypeError("timeout muss eine Zahl sein.")
    if timeout <= 0:
        raise ValueError("timeout muss groesser als 0 sein.")
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=float(timeout)):
            return True
    except OSError:
        return False


def https_head_reachable(url: str, timeout: float) -> bool:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url muss ein nicht-leerer String sein.")
    if not isinstance(timeout, (int, float)):
        raise TypeError("timeout muss eine Zahl sein.")
    if timeout <= 0:
        raise ValueError("timeout muss groesser als 0 sein.")
    request = urllib.request.Request(url=url, method="HEAD")
    try:
        with urllib.request.urlopen(
            request, timeout=float(timeout)
        ) as response:
            status = int(response.status)
            return status < int(HTTPStatus.INTERNAL_SERVER_ERROR)
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def has_internet(timeout: float = 2.0) -> bool:
    if timeout <= 0:
        raise ValueError("timeout muss groesser als 0 sein.")
    dns_ok = dns_reachable(timeout)
    https_targets = (
        "https://pypi.org/",
        "https://www.python.org/",
    )
    https_ok = any(
        https_head_reachable(target, timeout) for target in https_targets
    )
    return dns_ok or https_ok


def parse_os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    if not isinstance(path, Path):
        raise TypeError("path muss ein Path sein.")
    if not path.exists():
        LOGGER.debug("os-release nicht gefunden: %s", path)
        return {}
    if path.is_dir():
        LOGGER.warning("os-release Pfad ist ein Ordner statt Datei: %s", path)
        return {}
    data: dict[str, str] = {}
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        LOGGER.warning("os-release konnte nicht gelesen werden: %s", exc)
        return {}

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def detect_linux_distribution() -> dict[str, str]:
    data = parse_os_release()
    return {
        "id": data.get("ID", ""),
        "name": data.get("NAME", ""),
        "like": data.get("ID_LIKE", ""),
    }
