from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MANIFEST_SCHEMA_VERSION = "1"


@dataclass
class VerifyResult:
    ok: bool
    details: list[str]


def _tracked_files(project_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(project_root), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    files: list[Path] = []
    for line in result.stdout.splitlines():
        rel = Path(line.strip())
        if not rel.parts:
            continue
        files.append(rel)
    return sorted(files)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    project_root: Path,
    *,
    exclude: set[Path] | None = None,
) -> dict[str, object]:
    exclude = exclude or set()
    entries: list[dict[str, object]] = []
    for rel_path in _tracked_files(project_root):
        if rel_path in exclude:
            continue
        abs_path = project_root / rel_path
        entries.append(
            {
                "path": rel_path.as_posix(),
                "size": abs_path.stat().st_size,
                "sha256": _sha256(abs_path),
            }
        )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "files": entries,
    }


def write_manifest(project_root: Path, output: Path) -> Path:
    rel_output = output.relative_to(project_root)
    manifest = build_manifest(project_root, exclude={rel_output})
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output


def verify_manifest(project_root: Path, manifest_path: Path) -> VerifyResult:
    if not manifest_path.exists():
        return VerifyResult(False, [f"Manifest fehlt: {manifest_path}"])

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = build_manifest(
        project_root,
        exclude={manifest_path.relative_to(project_root)},
    )
    details: list[str] = []
    if data.get("schema_version") != expected["schema_version"]:
        details.append("Schema-Version stimmt nicht.")

    expected_files = cast(list[dict[str, object]], expected["files"])
    manifest_files = cast(list[dict[str, object]], data.get("files", []))

    current_files = {
        str(entry["path"]): (int(entry["size"]), str(entry["sha256"]))
        for entry in expected_files
    }
    stored_files = {
        str(entry["path"]): (int(entry["size"]), str(entry["sha256"]))
        for entry in manifest_files
    }

    missing = sorted(set(current_files) - set(stored_files))
    extra = sorted(set(stored_files) - set(current_files))
    changed = sorted(
        path
        for path in set(current_files) & set(stored_files)
        if current_files[path] != stored_files[path]
    )

    if missing:
        details.append(f"Fehlende Einträge: {', '.join(missing)}")
    if extra:
        details.append(f"Veraltete Einträge: {', '.join(extra)}")
    if changed:
        details.append(f"Dateien geändert: {', '.join(changed)}")

    return VerifyResult(ok=not details, details=details)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Erzeugt oder prüft eine JSON-Manifestdatei "
            "mit SHA256-Prüfsummen."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Projektwurzel (Standard: aktuelles Verzeichnis).",
    )
    parser.add_argument(
        "--output",
        default="data/manifest/v1/project_files.json",
        help="Pfad der Manifestdatei relativ zur Projektwurzel.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Manifestdatei prüfen statt neu schreiben.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    project_root = Path(args.project_root).resolve()
    output = (project_root / args.output).resolve()

    if args.verify:
        result = verify_manifest(project_root, output)
        if result.ok:
            print(f"Manifest ok: {output}")
            return 0
        for detail in result.details:
            print(detail)
        return 1

    path = write_manifest(project_root, output)
    print(f"Manifest geschrieben: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
