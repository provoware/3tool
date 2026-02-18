from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .paths import config_dir

CURRENT_SCHEMA_VERSION = 2
_CONFIG_FILE_NAME = "session_config.json"
_RUNTIME_CONFIG_SEGMENTS = ("runtime", "config")

_ALLOWED_PRESETS = {
    "ultrafast",
    "superfast",
    "veryfast",
    "faster",
    "fast",
    "medium",
    "slow",
    "slower",
    "veryslow",
}


@dataclass(frozen=True)
class Config:
    schema_version: int = CURRENT_SCHEMA_VERSION
    debug: bool = False
    simple_mode: bool = False
    default_width: int = 1920
    default_height: int = 1080
    default_crf: int = 23
    default_preset: str = "ultrafast"


def _runtime_config_dir(base_dir: Path | None = None) -> Path:
    base = base_dir or config_dir()
    return base.joinpath(*_RUNTIME_CONFIG_SEGMENTS)


def config_file_path(base_dir: Path | None = None) -> Path:
    return _runtime_config_dir(base_dir) / _CONFIG_FILE_NAME


def default_config() -> Config:
    return Config()


def _validate_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Ungueltiger Wert fuer '{name}': Erwartet bool.")
    return value


def _validate_int(
    name: str, value: Any, *, min_value: int, max_value: int
) -> int:
    if not isinstance(value, int):
        raise ValueError(f"Ungueltiger Wert fuer '{name}': Erwartet int.")
    if value < min_value or value > max_value:
        raise ValueError(
            f"Ungueltiger Wert fuer '{name}': {value} ausserhalb {min_value}-{max_value}."
        )
    return value


def _validate_preset(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(
            "Ungueltiger Wert fuer 'default_preset': Erwartet String."
        )
    preset = value.strip().lower()
    if preset not in _ALLOWED_PRESETS:
        allowed = ", ".join(sorted(_ALLOWED_PRESETS))
        raise ValueError(
            "Ungueltiger Wert fuer 'default_preset': "
            f"'{value}'. Erlaubt: {allowed}."
        )
    return preset


def validate_config_payload(payload: dict[str, Any]) -> Config:
    required_fields = {
        "schema_version",
        "debug",
        "simple_mode",
        "default_width",
        "default_height",
        "default_crf",
        "default_preset",
    }
    missing = sorted(required_fields - payload.keys())
    if missing:
        raise ValueError(
            "Konfiguration unvollstaendig. Fehlende Felder: "
            + ", ".join(missing)
        )

    schema_version = _validate_int(
        "schema_version",
        payload["schema_version"],
        min_value=1,
        max_value=CURRENT_SCHEMA_VERSION,
    )
    if schema_version != CURRENT_SCHEMA_VERSION:
        raise ValueError(
            "Konfigurationsschema wird nicht direkt unterstuetzt. "
            "Bitte zuerst Migration ausfuehren."
        )

    width = _validate_int(
        "default_width", payload["default_width"], min_value=320, max_value=7680
    )
    height = _validate_int(
        "default_height",
        payload["default_height"],
        min_value=240,
        max_value=4320,
    )
    crf = _validate_int(
        "default_crf", payload["default_crf"], min_value=0, max_value=51
    )

    return Config(
        schema_version=schema_version,
        debug=_validate_bool("debug", payload["debug"]),
        simple_mode=_validate_bool("simple_mode", payload["simple_mode"]),
        default_width=width,
        default_height=height,
        default_crf=crf,
        default_preset=_validate_preset(payload["default_preset"]),
    )


def _parse_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Konfiguration ist kein gueltiges JSON. "
            "Naechster Schritt: Datei pruefen oder neu erzeugen lassen."
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError("Konfiguration muss ein JSON-Objekt sein.")
    return raw


def _backup_file(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.stem}.v1-backup-{stamp}{path.suffix}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def _migrate_v1_to_v2(payload: dict[str, Any]) -> dict[str, Any]:
    migrated = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "debug": bool(payload.get("debug", False)),
        "simple_mode": bool(payload.get("simple_mode", False)),
        "default_width": payload.get("default_width", 1920),
        "default_height": payload.get("default_height", 1080),
        "default_crf": payload.get("default_crf", 23),
        "default_preset": payload.get("default_preset", "ultrafast"),
    }
    validated = validate_config_payload(migrated)
    return asdict(validated)


def migrate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    schema_version_raw = payload.get("schema_version", 1)
    if not isinstance(schema_version_raw, int):
        raise ValueError("schema_version muss eine ganze Zahl sein.")
    if schema_version_raw == CURRENT_SCHEMA_VERSION:
        validated = validate_config_payload(payload)
        return asdict(validated)
    if schema_version_raw == 1:
        return _migrate_v1_to_v2(payload)
    raise ValueError(f"Unbekannte schema_version: {schema_version_raw}.")


def save_config(config: Config, *, base_dir: Path | None = None) -> Path:
    target = config_file_path(base_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(validate_config_payload(asdict(config)))
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return target


def load_config(*, base_dir: Path | None = None) -> Config:
    path = config_file_path(base_dir)
    if not path.exists():
        config = default_config()
        save_config(config, base_dir=base_dir)
        return config

    raw_payload = _parse_json(path)
    try:
        migrated_payload = migrate_payload(raw_payload)
    except Exception as exc:
        raise ValueError(
            "Konfiguration konnte nicht geladen werden. "
            "Naechster Schritt: Backup wiederherstellen oder Datei loeschen."
        ) from exc

    if migrated_payload != raw_payload:
        backup_path = _backup_file(path)
        try:
            path.write_text(
                json.dumps(migrated_payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError:
            backup_path.replace(path)
            raise ValueError(
                "Migration fehlgeschlagen. Backup wurde zurueckgespielt."
            )

    return validate_config_payload(migrated_payload)


def apply_simple_mode_defaults(config: Config) -> Config:
    """Gibt ein neues Konfigobjekt mit ressourcenschonenden Defaults zurueck."""
    return Config(
        schema_version=config.schema_version,
        debug=config.debug,
        simple_mode=True,
        default_width=1280,
        default_height=720,
        default_crf=24,
        default_preset="veryfast",
    )
