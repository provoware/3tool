from __future__ import annotations

import argparse
import logging
from pathlib import Path

from core.launcher_checks import evaluate_release_readiness

LOGGER = logging.getLogger("videobatch_release_audit")


RECOMMENDED_COMMANDS = (
    "bash scripts/quality_check.sh",
    "pytest -q",
    "python videobatch_launcher.py --release-check",
)


def validate_project_root(project_root: Path) -> Path:
    if not isinstance(project_root, Path):
        raise TypeError("project_root muss ein Path sein.")
    root = project_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Projektpfad nicht gefunden: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Projektpfad ist kein Ordner: {root}")
    return root


def collect_release_gaps(project_root: Path) -> list[str]:
    root = validate_project_root(project_root)
    results = evaluate_release_readiness(root)
    gaps: list[str] = []
    for result in results:
        if not result.ok:
            gaps.append(
                f"{result.title}: {result.detail} -> {result.recommendation}"
            )
    return gaps


def render_report(project_root: Path) -> str:
    root = validate_project_root(project_root)
    gaps = collect_release_gaps(root)
    lines = [
        "Release-Audit (Freigabe-Prüfung):",
        f"Projekt: {root}",
        "",
    ]
    if gaps:
        lines.append("Es fehlen noch Punkte für ein fehlerfreies Release:")
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("Keine Lücken gefunden. Release-Basis ist bereit.")
    lines.extend(
        [
            "",
            "Empfohlene Prüf-Befehle:",
            *[f"- {command}" for command in RECOMMENDED_COMMANDS],
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft Release-Lücken in einfacher Sprache und zeigt klare "
            "nächste Schritte."
        )
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Projektordner (Standard: aktueller Ordner)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Liefert Exit-Code 1, wenn Lücken gefunden wurden.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    report = render_report(args.project_root)
    print(report)
    gaps = collect_release_gaps(args.project_root)
    if gaps:
        LOGGER.info("Release-Audit fand %d Lücke(n).", len(gaps))
        return 1 if args.strict else 0
    LOGGER.info("Release-Audit fand keine Lücken.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
