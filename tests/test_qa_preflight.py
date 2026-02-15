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


def test_validate_package_names_rejects_empty_and_duplicates() -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_package_names([])

    result = qa_preflight._validate_package_names(
        ["pytest", " pytest ", "mypy"]
    )

    assert result == ["pytest", "mypy"]


def test_run_quiet_rejects_invalid_command() -> None:
    with pytest.raises(ValueError):
        qa_preflight._run_quiet([], 1)


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
    monkeypatch.setattr(qa_preflight, "_network_reachable", lambda *_: True)
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
    monkeypatch.setattr(qa_preflight, "_network_reachable", lambda *_: True)
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


def test_validate_timeout_seconds_rejects_invalid_values() -> None:
    with pytest.raises(TypeError):
        qa_preflight._validate_timeout_seconds("3", "timeout")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        qa_preflight._validate_timeout_seconds(0, "timeout")


def test_network_reachable_validates_inputs() -> None:
    with pytest.raises(ValueError):
        qa_preflight._network_reachable("", 443, 3)
    with pytest.raises(TypeError):
        qa_preflight._network_reachable("pypi.org", "443", 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        qa_preflight._network_reachable("pypi.org", 70000, 3)


def test_network_reachable_returns_false_on_oserror(monkeypatch) -> None:
    def fail_connection(*_args, **_kwargs):
        raise OSError("offline")

    monkeypatch.setattr(
        qa_preflight.socket, "create_connection", fail_connection
    )

    assert qa_preflight._network_reachable("pypi.org", 443, 3) is False


def test_ensure_pip_with_fallback_returns_ready_when_pip_exists(
    monkeypatch,
) -> None:
    monkeypatch.setattr(qa_preflight, "_pip_available", lambda *_: True)

    ok, message = qa_preflight._ensure_pip_with_fallback(
        "python3",
        debug_mode=False,
    )

    assert ok is True
    assert "pip ist bereit" in message


def test_ensure_pip_with_fallback_repairs_with_ensurepip(monkeypatch) -> None:
    states = iter([False, True])
    monkeypatch.setattr(
        qa_preflight,
        "_pip_available",
        lambda *_: next(states),
    )
    monkeypatch.setattr(
        qa_preflight.subprocess,
        "check_call",
        lambda *_args, **_kwargs: None,
    )

    ok, message = qa_preflight._ensure_pip_with_fallback(
        "python3",
        debug_mode=True,
    )

    assert ok is True
    assert "automatisch repariert" in message


def test_ensure_pip_with_fallback_fails_when_ensurepip_errors(
    monkeypatch,
) -> None:
    monkeypatch.setattr(qa_preflight, "_pip_available", lambda *_: False)

    def fail_ensurepip(*_args, **_kwargs):
        raise subprocess.SubprocessError("ensurepip failed")

    monkeypatch.setattr(
        qa_preflight.subprocess,
        "check_call",
        fail_ensurepip,
    )

    ok, message = qa_preflight._ensure_pip_with_fallback(
        "python3",
        debug_mode=False,
    )

    assert ok is False
    assert "ensurepip fehlgeschlagen" in message


def test_run_preflight_fails_when_pip_not_repairable(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(
        qa_preflight,
        "_ensure_pip_with_fallback",
        lambda *_: (False, "pip kaputt"),
    )

    result = qa_preflight.run_preflight(req, ["pytest"], "python3")

    assert result == 1


def test_run_preflight_warns_when_network_unreachable(
    monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(qa_preflight, "_network_reachable", lambda *_: False)
    monkeypatch.setattr(qa_preflight, "_run_pip_install", lambda *_args: None)
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)

    result = qa_preflight.run_preflight(req, ["pytest"], "python3")

    assert result == 0
    captured = capsys.readouterr()
    assert "Netzwerk-Check: pypi.org aktuell nicht erreichbar" in captured.out
