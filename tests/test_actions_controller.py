from pathlib import Path

from gui.controllers.actions import (build_initial_state, resolve_text,
                                     validate_project_root_candidate)


def test_validate_project_root_candidate(tmp_path: Path) -> None:
    assert validate_project_root_candidate(tmp_path)
    assert not validate_project_root_candidate(tmp_path / "missing")


def test_resolve_text_uses_fallback() -> None:
    assert resolve_text({}, "x", "fallback") == "fallback"


def test_build_initial_state_rejects_non_paths() -> None:
    try:
        build_initial_state("/tmp/a", Path("/tmp/b"))  # type: ignore[arg-type]
    except TypeError:
        assert True
    else:
        assert False
