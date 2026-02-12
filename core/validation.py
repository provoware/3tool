from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.utils import build_out_name


DEFAULT_AUDIO_BITRATE = "192k"
DEFAULT_OUTPUT_TEMPLATE = (
    "{audio_name}_{video_laenge}_{zeitstempel}_{qualitaet}_{abmasse}_{form}.mp4"
)


@dataclass(frozen=True)
class FieldValidationResult:
    value: str
    is_valid: bool
    message: str = ""


def normalize_audio_bitrate(raw_value: str) -> FieldValidationResult:
    value = (raw_value or "").strip().replace(",", ".")
    if not value:
        return FieldValidationResult(
            value=DEFAULT_AUDIO_BITRATE,
            is_valid=True,
            message="Audiobitrate war leer und wurde auf 192k gesetzt.",
        )
    compact = re.sub(r"\s+", "", value)
    direct = re.fullmatch(r"(\d+)([kKmM])", compact)
    if direct:
        amount, unit = direct.groups()
        return FieldValidationResult(
            value=f"{int(amount)}{unit.lower() if unit.lower() == 'k' else 'M'}",
            is_valid=True,
        )
    text_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)\s*(kbps|kbit/s|kbit|mbps|mbit/s|mbit)",
        value.lower(),
    )
    if text_match:
        amount_text, unit_text = text_match.groups()
        amount = float(amount_text)
        if unit_text.startswith("k"):
            return FieldValidationResult(
                value=f"{max(1, int(round(amount)))}k",
                is_valid=True,
                message="Audiobitrate wurde automatisch in ffmpeg-Format umgewandelt.",
            )
        return FieldValidationResult(
            value=f"{max(1, int(round(amount)))}M",
            is_valid=True,
            message="Audiobitrate wurde automatisch in ffmpeg-Format umgewandelt.",
        )
    only_number = re.fullmatch(r"\d+", compact)
    if only_number:
        return FieldValidationResult(
            value=f"{compact}k",
            is_valid=True,
            message="Audiobitrate ohne Einheit erkannt, k wurde ergänzt.",
        )
    return FieldValidationResult(
        value=DEFAULT_AUDIO_BITRATE,
        is_valid=False,
        message=(
            "Bitte eine Audiobitrate wie 192k oder 2M eingeben. "
            "Die Zahl ist die Datenmenge pro Sekunde, k=Kilobit, M=Megabit."
        ),
    )


def validate_output_template(template: str) -> FieldValidationResult:
    cleaned = (template or "").strip() or DEFAULT_OUTPUT_TEMPLATE
    try:
        build_out_name("beispiel.mp3", Path.cwd(), cleaned)
    except ValueError as exc:
        return FieldValidationResult(
            value=DEFAULT_OUTPUT_TEMPLATE,
            is_valid=False,
            message=(
                f"{exc}\n"
                "Erlaubt sind: {audio_stem}, {audio_name}, {date}, {time}, "
                "{stamp}, {video_laenge}, {zeitstempel}, {qualitaet}, "
                "{abmasse}, {form}."
            ),
        )
    return FieldValidationResult(value=cleaned, is_valid=True)
