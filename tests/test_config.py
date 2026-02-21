from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.config import (
    CURRENT_SCHEMA_VERSION,
    Config,
    apply_simple_mode_defaults,
    config_file_path,
    load_config,
    save_config,
    validate_config_payload,
)


def test_load_config_creates_defaults_when_missing(tmp_path: Path) -> None:
    config = load_config(base_dir=tmp_path)

    assert config == Config()
    target = config_file_path(tmp_path)
    assert target.exists()


def test_load_config_rejects_corrupt_json(tmp_path: Path) -> None:
    target = config_file_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{kaputt", encoding="utf-8")

    with pytest.raises(ValueError, match="gueltiges JSON"):
        load_config(base_dir=tmp_path)


def test_validate_config_payload_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="Fehlende Felder"):
        validate_config_payload({"schema_version": CURRENT_SCHEMA_VERSION})


def test_validate_config_payload_rejects_invalid_values() -> None:
    payload = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "debug": False,
        "simple_mode": False,
        "default_width": -1,
        "default_height": 1080,
        "default_crf": 23,
        "default_preset": "ultrafast",
    }

    with pytest.raises(ValueError, match="default_width"):
        validate_config_payload(payload)


def test_load_config_migrates_v1_and_creates_backup(tmp_path: Path) -> None:
    target = config_file_path(tmp_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    v1_payload = {
        "debug": True,
        "simple_mode": False,
        "default_width": 1440,
        "default_height": 900,
        "default_crf": 20,
        "default_preset": "fast",
    }
    target.write_text(json.dumps(v1_payload), encoding="utf-8")

    config = load_config(base_dir=tmp_path)

    assert config.schema_version == CURRENT_SCHEMA_VERSION
    assert config.default_width == 1440
    backups = list(target.parent.glob("session_config.v1-backup-*.json"))
    assert backups


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    config = apply_simple_mode_defaults(Config(debug=True))

    save_config(config, base_dir=tmp_path)
    loaded = load_config(base_dir=tmp_path)

    assert loaded == config
