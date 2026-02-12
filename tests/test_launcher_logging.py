from pathlib import Path

from core import launcher_checks


def test_configure_logging_writes_log_file(tmp_path: Path) -> None:
    log_file = tmp_path / "logs" / "launcher.log"

    launcher_checks.configure_logging(log_file, debug=True)
    launcher_checks.LOGGER.debug("debug-eintrag")

    assert log_file.exists()
    text = log_file.read_text(encoding="utf-8")
    assert "debug-eintrag" in text
