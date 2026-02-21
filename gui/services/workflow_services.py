from __future__ import annotations

import logging
from pathlib import Path

from gui.state import PairRecord

LOGGER = logging.getLogger("VideoBatchTool")


class ValidationService:
    @staticmethod
    def validate_existing_paths(
        values: list[str], *, field_name: str
    ) -> list[str]:
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError("field_name muss gesetzt sein.")
        normalized: list[str] = []
        for value in values:
            path = Path(value).expanduser()
            if not path.exists():
                raise ValueError(
                    f"{field_name}: Datei fehlt ({path}). Nächster Schritt: Pfad prüfen."
                )
            normalized.append(str(path))
        LOGGER.debug("ValidationService: %s erfolgreich validiert", field_name)
        return normalized


class PairingService:
    @staticmethod
    def build_pairs(images: list[str], audios: list[str]) -> list[PairRecord]:
        if not isinstance(images, list) or not isinstance(audios, list):
            raise TypeError("images und audios müssen Listen sein.")
        pair_count = min(len(images), len(audios))
        result = [
            PairRecord(image_path=images[index], audio_path=audios[index])
            for index in range(pair_count)
        ]
        LOGGER.debug("PairingService: %d Paar(e) erstellt", len(result))
        return result


class ExportService:
    @staticmethod
    def build_export_targets(
        pairs: list[PairRecord],
        *,
        output_dir: Path,
        suffix: str = ".mp4",
    ) -> list[PairRecord]:
        if not isinstance(output_dir, Path):
            raise TypeError("output_dir muss Path sein.")
        output_dir.mkdir(parents=True, exist_ok=True)
        export_pairs: list[PairRecord] = []
        for index, pair in enumerate(pairs, start=1):
            if not isinstance(pair, PairRecord):
                raise TypeError("pairs darf nur PairRecord enthalten.")
            stem = Path(pair.image_path).stem or f"pair_{index:03d}"
            output_path = output_dir / f"{stem}{suffix}"
            export_pairs.append(
                PairRecord(
                    image_path=pair.image_path,
                    audio_path=pair.audio_path,
                    output_path=str(output_path),
                )
            )
        LOGGER.debug(
            "ExportService: %d Export-Ziel(e) erzeugt", len(export_pairs)
        )
        return export_pairs
