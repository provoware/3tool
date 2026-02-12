from __future__ import annotations

import subprocess
from pathlib import Path

from core import file_manifest


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=path,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def test_write_and_verify_manifest(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt", "b.txt"], cwd=tmp_path, check=True)

    manifest_path = tmp_path / "data/manifest/v1/project_files.json"
    file_manifest.write_manifest(tmp_path, manifest_path)

    result = file_manifest.verify_manifest(tmp_path, manifest_path)

    assert result.ok
    assert result.details == []


def test_verify_manifest_detects_change(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)

    manifest_path = tmp_path / "data/manifest/v1/project_files.json"
    file_manifest.write_manifest(tmp_path, manifest_path)
    (tmp_path / "a.txt").write_text("changed\n", encoding="utf-8")

    result = file_manifest.verify_manifest(tmp_path, manifest_path)

    assert not result.ok
    assert any("Dateien geändert" in detail for detail in result.details)
