from __future__ import annotations

from pathlib import Path
import subprocess

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


def test_validate_debug_mode_requires_bool() -> None:
    with pytest.raises(TypeError):
        qa_preflight._validate_debug_mode("ja")  # type: ignore[arg-type]


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


def test_run_preflight_debug_mode_prints_debug_lines(
    monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(qa_preflight, "_run_pip_install", lambda *_args: None)
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)

    result = qa_preflight.run_preflight(
        req,
        ["pytest"],
        "python3",
        debug_mode=True,
    )

    assert result == 0
    captured = capsys.readouterr()
    assert "🐞 Debug-Modus aktiv" in captured.out
    assert "🐞 Prüfe Tool-Import: pytest" in captured.out


def test_attempt_tool_repair_success(monkeypatch) -> None:
    installed_packages: list[str] = []

    def fake_install(packages: list[str], _python_cmd: str) -> None:
        installed_packages.extend(packages)

    monkeypatch.setattr(
        qa_preflight,
        "_run_pip_install_packages",
        fake_install,
    )
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_: True)

    unresolved = qa_preflight._attempt_tool_repair(
        ["pytest", "mypy"],
        "python3",
        debug_mode=False,
    )

    assert unresolved == []
    assert installed_packages == ["pytest", "mypy"]


def test_attempt_tool_repair_returns_unresolved_on_install_error(
    monkeypatch,
) -> None:
    def fail_install(_packages: list[str], _python_cmd: str) -> None:
        raise subprocess.SubprocessError("boom")

    monkeypatch.setattr(
        qa_preflight,
        "_run_pip_install_packages",
        fail_install,
    )

    unresolved = qa_preflight._attempt_tool_repair(
        ["pytest"],
        "python3",
        debug_mode=True,
    )

    assert unresolved == ["pytest"]


def test_install_requirements_with_fallback_uses_user_install(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight,
        "_run_pip_install",
        lambda *_: (_ for _ in ()).throw(
            subprocess.SubprocessError("no perms")
        ),
    )

    used_user = {"value": False}

    def fake_user_install(_requirements: Path, _python_cmd: str) -> None:
        used_user["value"] = True

    monkeypatch.setattr(
        qa_preflight, "_run_pip_install_user", fake_user_install
    )

    ok, message = qa_preflight._install_requirements_with_fallback(
        req,
        "python3",
        debug_mode=True,
    )

    assert ok is True
    assert used_user["value"] is True
    assert "--user" in message


def test_install_requirements_with_fallback_fails_after_user_install(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight,
        "_run_pip_install",
        lambda *_: (_ for _ in ()).throw(
            subprocess.SubprocessError("no perms")
        ),
    )
    monkeypatch.setattr(
        qa_preflight,
        "_run_pip_install_user",
        lambda *_: (_ for _ in ()).throw(subprocess.SubprocessError("offline")),
    )

    ok, message = qa_preflight._install_requirements_with_fallback(
        req,
        "python3",
        debug_mode=False,
    )

    assert ok is False
    assert "offline" in message
