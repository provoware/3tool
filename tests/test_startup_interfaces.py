from pathlib import Path

from core.launcher.models import CheckResult
from core.startup import apply_repairs, render_feedback, run_startup_checks


def test_render_feedback_includes_headline() -> None:
    rendered = render_feedback(
        [
            CheckResult(
                key="ok",
                title="Python",
                ok=True,
                detail="ok",
                blocking=True,
            )
        ]
    )
    assert "Start" in rendered


def test_run_startup_checks_validates_target_dir_type() -> None:
    try:
        run_startup_checks("python3", "bad", Path.cwd())  # type: ignore[arg-type]
    except TypeError as exc:
        assert "target_dir" in str(exc)
    else:
        raise AssertionError("TypeError erwartet")


def test_apply_repairs_returns_tuple(monkeypatch, tmp_path: Path) -> None:
    check = [
        CheckResult(
            key="ok",
            title="ok",
            ok=True,
            detail="ready",
            blocking=True,
        )
    ]

    monkeypatch.setattr(
        "core.startup.repair_orchestrator.run_startup_checks",
        lambda *_args, **_kwargs: check,
    )
    result_checks, repairs = apply_repairs("python3", tmp_path, tmp_path)
    assert result_checks == check
    assert repairs == []
