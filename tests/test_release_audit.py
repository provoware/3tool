from pathlib import Path

import pytest

from core import release_audit


def _write_release_basics(root: Path) -> None:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "quality_check.sh").write_text("#!/bin/bash\n")
    (root / "CHANGELOG.md").write_text("# Changelog\n")


def test_validate_project_root_rejects_non_path() -> None:
    with pytest.raises(TypeError):
        release_audit.validate_project_root(".")  # type: ignore[arg-type]


def test_collect_release_gaps_includes_open_todo(tmp_path: Path) -> None:
    _write_release_basics(tmp_path)
    (tmp_path / "todo.txt").write_text("- [ ] Offener Punkt\n")

    gaps = release_audit.collect_release_gaps(tmp_path)

    assert any("Offene Aufgaben" in gap for gap in gaps)


def test_collect_release_gaps_no_gaps_when_ready(tmp_path: Path) -> None:
    _write_release_basics(tmp_path)
    (tmp_path / "todo.txt").write_text("- [x] Fertig\n")

    gaps = release_audit.collect_release_gaps(tmp_path)

    assert gaps == []


def test_render_report_lists_commands(tmp_path: Path) -> None:
    _write_release_basics(tmp_path)
    (tmp_path / "todo.txt").write_text("- [x] Fertig\n")

    report = release_audit.render_report(tmp_path)

    assert "Empfohlene Prüf-Befehle:" in report
    assert "bash scripts/quality_check.sh" in report
