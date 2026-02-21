import pytest
import start_gui
from core.config import Config, apply_simple_mode_defaults


def test_simple_mode_defaults_applied() -> None:
    updated = apply_simple_mode_defaults(Config())

    assert updated.simple_mode is True
    assert updated.default_width == 1280
    assert updated.default_height == 720
    assert updated.default_crf == 24
    assert updated.default_preset == "veryfast"


def test_all_blocking_ok() -> None:
    py = start_gui.launcher_checks.check_python_version()
    assert start_gui._all_blocking_ok([py]) == py.ok


def test_prepare_runtime_dirs_uses_all_path_functions(
    monkeypatch, tmp_path
) -> None:
    base = tmp_path / "runtime"

    monkeypatch.setattr(start_gui, "user_data_dir", lambda: base / "data")
    monkeypatch.setattr(start_gui, "config_dir", lambda: base / "config")
    monkeypatch.setattr(start_gui, "log_dir", lambda: base / "logs")
    monkeypatch.setattr(start_gui, "work_dir", lambda: base / "work")
    monkeypatch.setattr(start_gui, "cache_dir", lambda: base / "cache")
    monkeypatch.setattr(
        start_gui.launcher_checks, "write_permissions_ok", lambda _: True
    )

    start_gui._prepare_runtime_dirs()

    for name in ("data", "config", "logs", "work", "cache"):
        assert (base / name).exists()


def test_print_check_summary_reports_counts(capsys) -> None:
    ok_result = start_gui.launcher_checks.CheckResult(
        key="ok",
        title="OK",
        ok=True,
        detail="ok",
        blocking=True,
    )
    fail_result = start_gui.launcher_checks.CheckResult(
        key="fail",
        title="FAIL",
        ok=False,
        detail="fail",
        blocking=True,
    )

    start_gui._print_check_summary([ok_result, fail_result])
    output = capsys.readouterr().out

    assert "1/2 ok" in output
    assert "1 blockierend" in output


def test_print_release_readiness_outputs_warning(capsys, monkeypatch) -> None:
    checks = [
        start_gui.launcher_checks.ReleaseReadinessResult(
            key="todo",
            title="Todo",
            ok=False,
            detail="Noch offen",
            recommendation="Bitte schließen",
        )
    ]
    monkeypatch.setattr(
        start_gui.launcher_checks,
        "evaluate_release_readiness",
        lambda project_root: checks,
    )

    ok = start_gui._print_release_readiness(start_gui.Path.cwd())
    output = capsys.readouterr().out

    assert not ok
    assert "Release noch nicht bereit" in output


def test_main_forwards_to_primary_entry(monkeypatch) -> None:
    class Args:
        auto_repair = False
        simple_mode = False
        debug = True
        release_check = False

    monkeypatch.setattr(start_gui, "parse_args", lambda: Args())

    captured: dict[str, list[str]] = {"args": []}

    def _fake_primary(argv: list[str]) -> int:
        captured["args"] = argv
        return 0

    monkeypatch.setattr("app.main", _fake_primary)

    with pytest.warns(DeprecationWarning, match="start_gui.py ist veraltet"):
        result = start_gui.main()

    assert result == 0
    assert captured["args"] == ["--mode", "gui", "--debug"]


def test_safe_prepare_runtime_dirs_wraps_oserror(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui,
        "_prepare_runtime_dirs",
        lambda: (_ for _ in ()).throw(OSError("readonly")),
    )

    try:
        start_gui._safe_prepare_runtime_dirs()
    except start_gui.LauncherError as exc:
        assert "Laufzeitordner" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_safe_prepare_runtime_dirs_validates_required_keys(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui,
        "_prepare_runtime_dirs",
        lambda: {"Nutzerdaten": start_gui.Path(".")},
    )

    try:
        start_gui._safe_prepare_runtime_dirs()
    except start_gui.LauncherError as exc:
        assert "Laufzeitordner fehlt" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_safe_run_checks_wraps_value_error(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui,
        "_run_checks",
        lambda _py, _target, _project_root: (_ for _ in ()).throw(
            ValueError("bad args")
        ),
    )

    try:
        start_gui._safe_run_checks("python", start_gui.Path("."))
    except start_gui.LauncherError as exc:
        assert "System-Checks" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_safe_ensure_venv_wraps_subprocess_error(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui.launcher_checks,
        "ensure_venv",
        lambda _project_root: (_ for _ in ()).throw(
            start_gui.subprocess.SubprocessError("boom")
        ),
    )

    try:
        start_gui._safe_ensure_venv()
    except start_gui.LauncherError as exc:
        assert "Python-Umgebung" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_safe_run_repairs_wraps_value_error(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui,
        "_run_repairs",
        lambda _py, _target, _project_root: (_ for _ in ()).throw(
            ValueError("broken")
        ),
    )

    try:
        start_gui._safe_run_repairs("python", start_gui.Path("."))
    except start_gui.LauncherError as exc:
        assert "Self-Repair" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_parse_args_supports_release_check(monkeypatch) -> None:
    monkeypatch.setattr(
        start_gui.sys,
        "argv",
        ["start_gui.py", "--release-check"],
    )

    args = start_gui.parse_args()

    assert args.release_check is True


def test_run_release_quality_check_returns_true_on_success(
    monkeypatch, tmp_path
) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    quality_script = scripts_dir / "quality_check.sh"
    quality_script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")

    class Completed:
        returncode = 0

    monkeypatch.setattr(
        start_gui.subprocess,
        "run",
        lambda *args, **kwargs: Completed(),
    )

    assert start_gui._run_release_quality_check(tmp_path) is True


def test_run_release_quality_check_warns_if_missing(capsys, tmp_path) -> None:
    assert start_gui._run_release_quality_check(tmp_path) is False
    output = capsys.readouterr().out
    assert "Release-Qualitätscheck nicht gefunden" in output


def test_print_feedback_block_prints_sections(capsys) -> None:
    feedback: start_gui.launcher_checks.CheckFeedback = {
        "headline": "Start bereit.",
        "summary": "Pflichtpruefungen erfolgreich: 3/3",
        "next_steps": ["Weiter mit Starten"],
        "beginner_terms": ["pip (Paketmanager): installiert Pakete."],
        "quick_commands": ["python3 -m pip --version"],
    }

    start_gui._print_feedback_block(feedback)
    output = capsys.readouterr().out

    assert "Start bereit." in output
    assert "Schnellbefehle" in output


def test_dependency_bootstrap_runs_repairs_and_returns_ready(
    monkeypatch,
) -> None:
    first = [
        start_gui.launcher_checks.CheckResult(
            key="fail",
            title="Fail",
            ok=False,
            detail="blocked",
            blocking=True,
        )
    ]
    second = [
        start_gui.launcher_checks.CheckResult(
            key="ok",
            title="OK",
            ok=True,
            detail="ready",
            blocking=True,
        )
    ]
    state = {"count": 0}

    def fake_safe_run_checks(_py: str, _target, _project_root):
        state["count"] += 1
        return first if state["count"] == 1 else second

    monkeypatch.setattr(start_gui, "_safe_run_checks", fake_safe_run_checks)
    monkeypatch.setattr(start_gui, "_safe_run_repairs", lambda *_args: [])
    monkeypatch.setattr(start_gui, "_print_check_summary", lambda *_args: None)
    monkeypatch.setattr(start_gui, "_print_feedback_block", lambda *_args: None)

    result = start_gui._dependency_bootstrap("python3", start_gui.Path("."))

    assert result == second
    assert state["count"] == 2


def test_dependency_bootstrap_fails_if_still_blocked(monkeypatch) -> None:
    blocked = [
        start_gui.launcher_checks.CheckResult(
            key="fail",
            title="Fail",
            ok=False,
            detail="blocked",
            blocking=True,
        )
    ]

    monkeypatch.setattr(start_gui, "_safe_run_checks", lambda *_args: blocked)
    monkeypatch.setattr(start_gui, "_safe_run_repairs", lambda *_args: [])
    monkeypatch.setattr(start_gui, "_print_check_summary", lambda *_args: None)
    monkeypatch.setattr(start_gui, "_print_feedback_block", lambda *_args: None)

    try:
        start_gui._dependency_bootstrap("python3", start_gui.Path("."))
    except start_gui.LauncherError as exc:
        assert "Start abgebrochen" in str(exc)
    else:
        raise AssertionError("LauncherError erwartet")


def test_import_module_raises_launcher_error_for_missing_tool(
    monkeypatch,
) -> None:
    def _raise(_name: str):
        raise ModuleNotFoundError("No module named 'PySide6'")

    monkeypatch.setattr(start_gui.importlib, "import_module", _raise)

    try:
        start_gui._import_module("videobatch_gui")
    except start_gui.LauncherError as exc:
        message = str(exc)
        assert "Ursache" in message
        assert (
            "Befehl: python3 videobatch_extra.py --self-repair --debug"
            in message
        )
    else:
        raise AssertionError("LauncherError expected")


def test_start_gui_raises_launcher_error_for_subprocess_failure() -> None:
    def _start() -> None:
        raise start_gui.subprocess.SubprocessError("tool failed")

    try:
        start_gui._start_gui(_start)
    except start_gui.LauncherError as exc:
        message = str(exc)
        assert "Die Oberfläche konnte nicht gestartet werden" in message
        assert "Befehl: python3 videobatch_extra.py --selftest" in message
    else:
        raise AssertionError("LauncherError expected")
