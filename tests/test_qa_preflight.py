from __future__ import annotations

from pathlib import Path

import pytest

from core import qa_preflight


def test_validate_tool_names_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_tool_names(["unknown"])


def test_validate_requirements_path_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_requirements_path(tmp_path / "missing.txt")


def test_run_preflight_rejects_empty_python_cmd(tmp_path: Path) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("", encoding="utf-8")

    with pytest.raises(ValueError):
        qa_preflight.run_preflight(req, ["pytest"], "")


def test_run_preflight_reports_missing_python(tmp_path: Path) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("", encoding="utf-8")

    result = qa_preflight.run_preflight(
        req,
        ["pytest"],
        "python-that-does-not-exist-qa",
    )

    assert result == 1


def test_run_preflight_success(monkeypatch, tmp_path: Path) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(qa_preflight, "_run_pip_install", lambda *_args: None)
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)

    result = qa_preflight.run_preflight(req, ["pytest", "mypy"], "python3")

    assert result == 0
