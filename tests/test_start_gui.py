from core.config import apply_simple_mode_defaults, cfg
import start_gui


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
