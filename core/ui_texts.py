from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

ARCHIVE_VERSION = "v1"
DEFAULT_LOCALE = "de"
TEXT_ARCHIVE_DIR = Path(__file__).resolve().parent.parent / "data" / "texts"


def _flatten(prefix: str, value: Any, target: Dict[str, str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            _flatten(new_prefix, item, target)
        return
    if isinstance(value, str) and prefix:
        target[prefix] = value


def load_ui_texts(
    logger: logging.Logger | None = None,
    locale: str = DEFAULT_LOCALE,
    version: str = ARCHIVE_VERSION,
) -> Dict[str, str]:
    path = TEXT_ARCHIVE_DIR / version / f"{locale}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:  # pragma: no cover - fallback path
        if logger:
            logger.warning(
                "ui_texts.archive_missing",
                extra={"path": str(path), "error": str(exc)},
            )
        return {}
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:  # pragma: no cover - fallback path
        if logger:
            logger.warning(
                "ui_texts.archive_invalid",
                extra={"path": str(path), "error": str(exc)},
            )
        return {}
    flat: Dict[str, str] = {}
    _flatten("", payload, flat)
    return flat


def text_with_fallback(texts: Dict[str, str], key: str, fallback: str) -> str:
    value = texts.get(key, "").strip()
    return value if value else fallback


def text_with_format(
    texts: Dict[str, str],
    key: str,
    fallback: str,
    **values: Any,
) -> str:
    template = text_with_fallback(texts, key, fallback)
    if not isinstance(template, str) or not template.strip():
        raise ValueError("Textvorlage darf nicht leer sein.")
    for field, field_value in values.items():
        if not isinstance(field, str) or not field:
            raise ValueError("Formatfelder muessen gueltige Namen haben.")
        if field_value is None:
            raise ValueError(f"Formatfeld '{field}' darf nicht None sein.")
    try:
        return template.format(**values)
    except KeyError as exc:
        missing = str(exc).strip("'")
        raise ValueError(
            f"Textvorlage '{key}' erwartet fehlendes Feld: {missing}."
        ) from exc
