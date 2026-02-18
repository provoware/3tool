from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core import qa_preflight


def test_validate_tool_names_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_tool_names(["unknown"])


def test_validate_tool_names_rejects_empty_list() -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_tool_names([])


def test_validate_tool_names_deduplicates_preserving_order() -> None:
    assert qa_preflight._validate_tool_names(
        ["pytest", " pytest ", "mypy"]
    ) == [
        "pytest",
        "mypy",
    ]


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


def test_manual_recovery_commands_include_expected_entries(
    tmp_path: Path,
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    commands = qa_preflight._manual_recovery_commands(
        "python3",
        req,
        ["pytest", "mypy"],
    )

    assert commands[0] == "python3 -m pip install --upgrade pip"
    assert commands[1] == f"python3 -m pip install -r {req}"
    assert commands[2] == f"python3 -m pip install --user -r {req}"
    assert commands[3] == "python3 -m pip install --upgrade pytest mypy"


def test_manual_recovery_commands_quotes_paths_and_tools(
    tmp_path: Path,
) -> None:
    req = tmp_path / "requirements with spaces.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    commands = qa_preflight._manual_recovery_commands(
        "python3",
        req,
        ["pytest", "black"],
    )

    assert "requirements with spaces.txt" in commands[1]
    assert "'" in commands[1]
    assert commands[3].endswith("pytest black")


def test_novice_recovery_steps_include_simple_explanations(
    tmp_path: Path,
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    steps = qa_preflight._novice_recovery_steps(
        "Bitte nacheinander ausführen:",
        "python3",
        req,
        ["pytest", "mypy"],
    )

    assert steps[0] == "Bitte nacheinander ausführen:"
    assert "Interpreter (Python-Starter)" in steps[1]
    assert "pip = Installationswerkzeug" in steps[3]
    assert "python3 -m pip install --upgrade pytest mypy" in steps[-1]


def test_novice_recovery_steps_reject_empty_title(tmp_path: Path) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    with pytest.raises(ValueError):
        qa_preflight._novice_recovery_steps(
            "   ",
            "python3",
            req,
            ["pytest"],
        )


def test_network_any_reachable_validates_endpoints() -> None:
    with pytest.raises(ValueError):
        qa_preflight._network_any_reachable((), 3)


def test_network_any_reachable_returns_first_reachable(monkeypatch) -> None:
    monkeypatch.setattr(
        qa_preflight,
        "_network_reachable",
        lambda host, _port, _timeout: host == "files.pythonhosted.org",
    )

    ok, detail = qa_preflight._network_any_reachable(
        (("pypi.org", 443), ("files.pythonhosted.org", 443)),
        3,
    )

    assert ok is True
    assert detail == "files.pythonhosted.org:443"


def test_network_any_reachable_returns_checked_hosts_when_none_reachable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        qa_preflight,
        "_network_reachable",
        lambda *_args: False,
    )

    ok, detail = qa_preflight._network_any_reachable(
        (("pypi.org", 443), ("files.pythonhosted.org", 443)),
        3,
    )

    assert ok is False
    assert detail == "pypi.org:443, files.pythonhosted.org:443"


def test_run_quiet_rejects_invalid_command() -> None:
    with pytest.raises(ValueError):
        qa_preflight._run_quiet([], 1)


def test_validate_command_strips_parts() -> None:
    assert qa_preflight._validate_command([" python3 ", " -m ", " pip "]) == [
        "python3",
        "-m",
        "pip",
    ]


def test_tool_command_ok_accepts_binary_from_path(monkeypatch) -> None:
    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _name: "/usr/bin/ruff"
    )

    assert qa_preflight._tool_command_ok("ruff", "python3") is True


def test_tool_command_ok_falls_back_to_python_module(monkeypatch) -> None:
    monkeypatch.setattr(qa_preflight.shutil, "which", lambda _name: None)
    monkeypatch.setattr(qa_preflight, "_run_quiet", lambda *_args: True)

    assert qa_preflight._tool_command_ok("pytest", "python3") is True


def test_tool_command_ok_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        qa_preflight._tool_command_ok("   ", "python3")


def test_tool_command_ok_returns_false_for_unknown_tool(monkeypatch) -> None:
    monkeypatch.setattr(qa_preflight.shutil, "which", lambda _name: None)

    assert qa_preflight._tool_command_ok("not-supported", "python3") is False


def test_print_novice_recovery_steps_prints_and_returns(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    steps = qa_preflight._print_novice_recovery_steps(
        "python3",
        req,
        ["pytest"],
    )

    assert steps[0] == "Bitte nacheinander ausführen:"
    out = capsys.readouterr().out
    assert "Lösungsvorschläge" in out
    assert "python3 -m pip install --upgrade pytest" in out


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


def test_run_preflight_offline_skips_install_when_tools_available(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(qa_preflight, "_network_reachable", lambda *_: False)
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)

    called = {"value": False}

    def fail_install(*_args, **_kwargs):
        called["value"] = True
        raise AssertionError(
            "Install should be skipped offline when tools exist"
        )

    monkeypatch.setattr(qa_preflight, "_run_pip_install", fail_install)

    result = qa_preflight.run_preflight(req, ["pytest"], "python3")

    assert result == 0
    assert called["value"] is False


def test_run_preflight_offline_with_missing_tools_keeps_install_path(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(qa_preflight, "_network_reachable", lambda *_: False)

    calls = {"count": 0}

    def selective_import(module_name: str, _python_cmd: str) -> bool:
        if module_name != "pytest":
            return True
        return calls["count"] > 0

    def mark_install(*_args, **_kwargs) -> None:
        calls["count"] += 1

    monkeypatch.setattr(qa_preflight, "_module_import_ok", selective_import)
    monkeypatch.setattr(qa_preflight, "_run_pip_install", mark_install)

    result = qa_preflight.run_preflight(req, ["pytest"], "python3")

    assert result == 0
    assert calls["count"] == 1


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
    assert "Netzwerk-Check: Ziele nicht erreichbar" in captured.out


def test_validate_report_path_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        qa_preflight._validate_report_path(tmp_path)


def test_validate_validate_only_requires_bool() -> None:
    with pytest.raises(TypeError):
        qa_preflight._validate_validate_only("ja")  # type: ignore[arg-type]


def test_resolve_cli_tools_uses_profile_when_tools_not_set() -> None:
    tools = qa_preflight._resolve_cli_tools("quick", None)

    assert tools == ["ruff", "black", "pytest"]


def test_resolve_cli_tools_prefers_explicit_tools() -> None:
    tools = qa_preflight._resolve_cli_tools("quick", ["pytest", "mypy"])

    assert tools == ["pytest", "mypy"]


def test_resolve_cli_tools_rejects_unknown_profile() -> None:
    with pytest.raises(ValueError):
        qa_preflight._resolve_cli_tools("unknown", None)


def test_main_list_tools_outputs_profiles(
    monkeypatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        qa_preflight,
        "_parse_args",
        lambda: type(
            "Args",
            (),
            {
                "requirements": "requirements-dev.txt",
                "python": "python3",
                "tools": None,
                "profile": "standard",
                "list_tools": True,
                "validate_only": False,
                "debug": False,
                "report_json": "",
            },
        )(),
    )

    result = qa_preflight.main()

    assert result == 0
    out = capsys.readouterr().out
    assert "Unterstützte QA-Tools" in out
    assert "Profile:" in out


def test_run_preflight_validate_only_skips_install_and_repair(
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
        lambda *_: (True, "pip ist bereit"),
    )
    monkeypatch.setattr(
        qa_preflight,
        "_network_any_reachable",
        lambda *_: (True, "pypi.org:443"),
    )
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)

    install_called = {"value": False}
    repair_called = {"value": False}

    def fail_install(*_args, **_kwargs):
        install_called["value"] = True
        raise AssertionError("Install should not run in validate-only mode")

    def fail_repair(*_args, **_kwargs):
        repair_called["value"] = True
        raise AssertionError("Repair should not run in validate-only mode")

    monkeypatch.setattr(
        qa_preflight, "_install_requirements_with_fallback", fail_install
    )
    monkeypatch.setattr(qa_preflight, "_attempt_tool_repair", fail_repair)

    result = qa_preflight.run_preflight(
        req,
        ["pytest"],
        "python3",
        validate_only=True,
    )

    assert result == 0
    assert install_called["value"] is False
    assert repair_called["value"] is False


def test_run_preflight_fails_when_tool_command_missing(
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
        lambda *_: (True, "pip ist bereit"),
    )
    monkeypatch.setattr(
        qa_preflight,
        "_network_any_reachable",
        lambda *_: (True, "pypi.org:443"),
    )
    monkeypatch.setattr(qa_preflight, "_module_import_ok", lambda *_args: True)
    monkeypatch.setattr(
        qa_preflight,
        "_install_requirements_with_fallback",
        lambda *_args: (True, "ok"),
    )
    monkeypatch.setattr(qa_preflight, "_tool_command_ok", lambda *_args: False)
    monkeypatch.setattr(
        qa_preflight,
        "_attempt_tool_repair",
        lambda failed_tools, *_args: failed_tools,
    )

    result = qa_preflight.run_preflight(req, ["pytest"], "python3")

    assert result == 1


def test_write_preflight_report_writes_json(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "qa_report.json"

    qa_preflight._write_preflight_report(
        report_path,
        {"result": "success", "checks": []},
    )

    assert report_path.exists()
    written = report_path.read_text(encoding="utf-8")
    assert '"result": "success"' in written


def test_run_preflight_writes_json_report_on_success(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")
    report_path = tmp_path / "qa_report.json"

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
        report_path=report_path,
    )

    assert result == 0
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert '"result": "success"' in report_text
    assert '"tool:pytest"' in report_text


def test_run_preflight_writes_json_report_on_failure(
    monkeypatch, tmp_path: Path
) -> None:
    req = tmp_path / "requirements-dev.txt"
    req.write_text("pytest==9.0.2\n", encoding="utf-8")
    report_path = tmp_path / "qa_report_failed.json"

    monkeypatch.setattr(
        qa_preflight.shutil, "which", lambda _cmd: "/usr/bin/python3"
    )
    monkeypatch.setattr(
        qa_preflight,
        "_ensure_pip_with_fallback",
        lambda *_: (False, "pip kaputt"),
    )

    result = qa_preflight.run_preflight(
        req,
        ["pytest"],
        "python3",
        report_path=report_path,
    )

    assert result == 1
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert '"result": "failed"' in report_text
    assert "pip-Unterstützung" in report_text


def test_parse_args_uses_standard_profile_when_no_tools_are_passed(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        qa_preflight.sys,
        "argv",
        ["qa_preflight"],
    )

    args = qa_preflight._parse_args()

    assert args.tools is None
    assert args.profile == "standard"
    assert args.report_json == ""


def test_default_qa_tools_are_supported() -> None:
    assert (
        qa_preflight._validate_tool_names(qa_preflight.DEFAULT_QA_TOOLS)
        == qa_preflight.DEFAULT_QA_TOOLS
    )


def test_python_not_found_help_contains_actionable_commands() -> None:
    steps = qa_preflight._python_not_found_help("python3")

    assert "Interpreterpfad" in steps[0]
    assert steps[1] == "Schnelltest im Terminal:"
    assert steps[2] == "- python3 --version"
    assert steps[3] == "- which python3"
