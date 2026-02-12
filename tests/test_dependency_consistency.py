from __future__ import annotations

from pathlib import Path

from core import dependency_consistency


def test_dependency_check_ok(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "\n".join(dependency_consistency.RUNTIME_PACKAGES) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "requirements-dev.txt").write_text(
        "\n".join(dependency_consistency.DEV_PACKAGES) + "\n",
        encoding="utf-8",
    )

    result = dependency_consistency.check_files(tmp_path)

    assert result.ok
    assert result.details == []


def test_dependency_check_reports_missing_and_duplicates(
    tmp_path: Path,
) -> None:
    (tmp_path / "requirements.txt").write_text("PySide6\n", encoding="utf-8")
    (tmp_path / "requirements-dev.txt").write_text(
        "black==24.8.0\nblack==24.8.0\n",
        encoding="utf-8",
    )

    result = dependency_consistency.check_files(tmp_path)

    assert not result.ok
    assert any("Laufzeitpakete" in detail for detail in result.details)
    assert any("Dev-Pakete" in detail for detail in result.details)
    assert any("Doppelte" in detail for detail in result.details)
