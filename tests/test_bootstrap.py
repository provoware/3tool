from __future__ import annotations

import json
from pathlib import Path

import pytest

from core import bootstrap
from core.launcher.models import CheckResult, RepairResult


def _ok_check() -> CheckResult:
    return CheckResult(
        key="ok",
        title="OK",
        ok=True,
        detail="ready",
        blocking=True,
    )


def _failed_check() -> CheckResult:
    return CheckResult(
        key="fail",
        title="FAIL",
        ok=False,
        detail="broken",
        fix_hint="repair",
        blocking=True,
    )


def test_run_preflight_validates_inputs(tmp_path: Path) -> None:
    with pytest.raises(bootstrap.BootstrapError):
        bootstrap.run_preflight("", tmp_path, tmp_path)

    with pytest.raises(bootstrap.BootstrapError):
        bootstrap.run_preflight("python3", "bad", tmp_path)  # type: ignore[arg-type]

    with pytest.raises(bootstrap.BootstrapError):
        bootstrap.run_preflight("python3", tmp_path, "bad")  # type: ignore[arg-type]


def test_run_preflight_writes_success_report(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "collect_checks",
        lambda *_args, **_kwargs: [_ok_check()],
    )

    bootstrap.run_preflight("python3", tmp_path, tmp_path)

    report_path = tmp_path / "logs" / "startup_preflight_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["status"] == "ok"
    assert payload["checks_before"][0]["ok"] is True
    assert payload["checks_after"][0]["ok"] is True
    assert payload["repair_feedback"]["summary"]


def test_run_preflight_writes_repaired_report(
    monkeypatch,
    tmp_path: Path,
) -> None:
    checks_state = {"call": 0}

    def _collect(*_args, **_kwargs):
        checks_state["call"] += 1
        if checks_state["call"] == 1:
            return [_failed_check()]
        return [_ok_check()]

    monkeypatch.setattr(bootstrap.launcher_checks, "collect_checks", _collect)
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "run_repairs",
        lambda *_args, **_kwargs: [
            RepairResult(
                key="packages",
                title="Pakete",
                ok=True,
                detail="installiert",
            )
        ],
    )

    bootstrap.run_preflight("python3", tmp_path, tmp_path)

    report_path = tmp_path / "logs" / "startup_preflight_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["status"] == "repaired"
    assert payload["checks_before"][0]["ok"] is False
    assert payload["checks_after"][0]["ok"] is True


def test_run_preflight_report_contains_context_fields(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "collect_checks",
        lambda *_args, **_kwargs: [_ok_check()],
    )

    bootstrap.run_preflight("python3", tmp_path, tmp_path)

    report_path = tmp_path / "logs" / "startup_preflight_report.json"
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["python_cmd"] == "python3"
    assert payload["project_root"] == str(tmp_path)
    assert payload["report_path"] == str(report_path)
    assert payload["generated_at"]
    assert payload["next_actions"]


def test_run_preflight_rejects_empty_checks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "collect_checks",
        lambda *_args, **_kwargs: [],
    )

    with pytest.raises(bootstrap.BootstrapError) as exc_info:
        bootstrap.run_preflight("python3", tmp_path, tmp_path)

    assert "keine Ergebnisse" in str(exc_info.value)


def test_run_preflight_rejects_invalid_repair_result(
    monkeypatch,
    tmp_path: Path,
) -> None:
    checks_state = {"call": 0}

    def _collect(*_args, **_kwargs):
        checks_state["call"] += 1
        if checks_state["call"] == 1:
            return [_failed_check()]
        return [_ok_check()]

    monkeypatch.setattr(bootstrap.launcher_checks, "collect_checks", _collect)
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "run_repairs",
        lambda *_args, **_kwargs: ["ungueltig"],
    )

    with pytest.raises(bootstrap.BootstrapError) as exc_info:
        bootstrap.run_preflight("python3", tmp_path, tmp_path)

    assert "ungueltige Ergebnisse" in str(exc_info.value)


def test_run_preflight_failure_mentions_report_path(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "collect_checks",
        lambda *_args, **_kwargs: [_failed_check()],
    )
    monkeypatch.setattr(
        bootstrap.launcher_checks,
        "run_repairs",
        lambda *_args, **_kwargs: [
            RepairResult(
                key="packages",
                title="Pakete",
                ok=False,
                detail="noch kaputt",
            )
        ],
    )

    with pytest.raises(bootstrap.BootstrapError) as exc_info:
        bootstrap.run_preflight("python3", tmp_path, tmp_path)

    message = str(exc_info.value)
    report_path = tmp_path / "logs" / "startup_preflight_report.json"
    assert str(report_path) in message

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert payload["checks_before"][0]["ok"] is False
    assert payload["checks_after"][0]["ok"] is False
