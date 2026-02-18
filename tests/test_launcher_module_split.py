from pathlib import Path

import pytest

from core.launcher import checks, feedback, network
from core.launcher.models import CheckResult, RepairResult


def test_network_timeout_validation() -> None:
    with pytest.raises(ValueError):
        network.has_internet(0)


def test_checks_write_permissions_type_guard() -> None:
    with pytest.raises(TypeError):
        checks.write_permissions_ok("x")  # type: ignore[arg-type]


def test_feedback_build_check_feedback_extracts_commands() -> None:
    results = [
        CheckResult(
            key="pip",
            title="pip",
            ok=False,
            detail="fehlt",
            fix_hint="Befehl: python -m ensurepip --upgrade",
        )
    ]
    built = feedback.build_check_feedback(results)
    assert built["headline"].startswith("Start")
    assert built["quick_commands"] == ["python -m ensurepip --upgrade"]


def test_feedback_recovery_hints_include_offline_hint() -> None:
    hints = feedback.beginner_recovery_hints(
        [
            RepairResult(
                key="packages",
                title="Pakete",
                ok=False,
                detail="fehlt",
                skipped_offline=True,
            )
        ]
    )
    assert any("Offline" in hint for hint in hints)


def test_parse_os_release_handles_missing_file(tmp_path: Path) -> None:
    assert network.parse_os_release(tmp_path / "missing") == {}
