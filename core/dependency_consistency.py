from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

RUNTIME_PACKAGES = ("PySide6", "Pillow", "ffmpeg-python")
DEV_PACKAGES = (
    "black==24.8.0",
    "ruff==0.6.9",
    "mypy==1.19.1",
    "pytest==9.0.2",
    "flake8==7.1.1",
    "isort==5.13.2",
    "autoflake==2.3.1",
)


@dataclass(frozen=True)
class DependencyCheck:
    ok: bool
    details: list[str]


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    entries: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    return entries


def _as_name(entry: str) -> str:
    return entry.split("==", 1)[0].strip().lower()


def check_files(project_root: Path) -> DependencyCheck:
    req_path = project_root / "requirements.txt"
    req_dev_path = project_root / "requirements-dev.txt"

    runtime_entries = _read_lines(req_path)
    dev_entries = _read_lines(req_dev_path)

    details: list[str] = []

    expected_runtime = {_as_name(pkg) for pkg in RUNTIME_PACKAGES}
    actual_runtime = {_as_name(pkg) for pkg in runtime_entries}
    missing_runtime = sorted(expected_runtime - actual_runtime)
    if missing_runtime:
        details.append(
            "Fehlende Laufzeitpakete in requirements.txt: "
            + ", ".join(missing_runtime)
        )

    expected_dev_exact = set(DEV_PACKAGES)
    actual_dev_exact = set(dev_entries)
    missing_dev = sorted(expected_dev_exact - actual_dev_exact)
    if missing_dev:
        details.append(
            "Fehlende oder unpinnte Dev-Pakete in requirements-dev.txt: "
            + ", ".join(missing_dev)
        )

    duplicate_names = sorted(
        {
            name
            for name in [_as_name(item) for item in dev_entries]
            if [_as_name(x) for x in dev_entries].count(name) > 1
        }
    )
    if duplicate_names:
        details.append(
            "Doppelte Dev-Pakete in requirements-dev.txt: "
            + ", ".join(duplicate_names)
        )

    return DependencyCheck(ok=not details, details=details)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prueft die Konsistenz von requirements-Dateien."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Projektordner (Standard: aktueller Ordner)",
    )
    args = parser.parse_args()

    result = check_files(args.project_root)
    if result.ok:
        print("✅ Abhaengigkeitskonsistenz ist in Ordnung.")
        return 0

    print("❌ Abhaengigkeitskonsistenz fehlerhaft:")
    for detail in result.details:
        print(f" - {detail}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
