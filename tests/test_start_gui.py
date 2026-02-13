import start_gui
from core.config import apply_simple_mode_defaults, cfg


def test_simple_mode_defaults_applied() -> None:
    cfg.default_width = 1920
    cfg.default_height = 1080
    cfg.default_crf = 23
    cfg.default_preset = "ultrafast"
    cfg.simple_mode = False

    apply_simple_mode_defaults()

    assert cfg.simple_mode is True
    assert cfg.default_width == 1280
    assert cfg.default_height == 720
    assert cfg.default_crf == 24
    assert cfg.default_preset == "veryfast"


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


def test_main_runs_auto_repair_even_without_flag(monkeypatch) -> None:
    calls = {"repairs": 0}

    class Args:
        auto_repair = False
        simple_mode = False
        debug = False

    monkeypatch.setattr(start_gui, "parse_args", lambda: Args())
    monkeypatch.setattr(start_gui, "_ensure_files", lambda: None)
    monkeypatch.setattr(
        start_gui,
        "_prepare_runtime_dirs",
        lambda: {
            "Nutzerdaten": start_gui.Path("."),
            "Protokolle": start_gui.Path("."),
        },
    )
    monkeypatch.setattr(
        start_gui.launcher_checks, "configure_logging", lambda *_args: None
    )
    monkeypatch.setattr(start_gui.launcher_checks, "ensure_venv", lambda: None)
    monkeypatch.setattr(
        start_gui.launcher_checks,
        "venv_python",
        lambda: start_gui.Path("python3"),
    )
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

    def fake_run_checks(_py: str, _target):
        state["count"] += 1
        return first if state["count"] == 1 else second

    monkeypatch.setattr(start_gui, "_run_checks", fake_run_checks)

    def fake_run_repairs(_py: str, _target):
        calls["repairs"] += 1
        return []

    monkeypatch.setattr(start_gui, "_run_repairs", fake_run_repairs)
    monkeypatch.setattr(start_gui, "_print_check_summary", lambda *_args: None)
    monkeypatch.setattr(
        start_gui, "_print_release_readiness", lambda *_args: True
    )
    monkeypatch.setattr(start_gui, "_print_beginner_tips", lambda: None)
    monkeypatch.setattr(
        start_gui,
        "_import_module",
        lambda _name: type(
            "GUI", (), {"run_gui": staticmethod(lambda: None)}
        )(),
    )

    result = start_gui.main()

    assert result == 0
    assert calls["repairs"] == 1
