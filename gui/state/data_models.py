from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging

LOGGER = logging.getLogger("VideoBatchTool")


def _normalize_path(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Pfad muss ein String sein.")
    normalized = value.strip()
    if not normalized:
        raise ValueError("Pfad darf nicht leer sein.")
    return str(Path(normalized).expanduser())


@dataclass(frozen=True)
class PairRecord:
    image_path: str
    audio_path: str
    output_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_path", _normalize_path(self.image_path))
        object.__setattr__(self, "audio_path", _normalize_path(self.audio_path))
        if self.output_path is not None:
            object.__setattr__(
                self,
                "output_path",
                _normalize_path(self.output_path),
            )


@dataclass
class ImagesModel:
    items: list[str] = field(default_factory=list)

    def set_items(self, values: list[str]) -> list[str]:
        self.items = [_normalize_path(value) for value in values]
        LOGGER.debug("ImagesModel aktualisiert: %d Eintraege", len(self.items))
        return list(self.items)


@dataclass
class AudiosModel:
    items: list[str] = field(default_factory=list)

    def set_items(self, values: list[str]) -> list[str]:
        self.items = [_normalize_path(value) for value in values]
        LOGGER.debug("AudiosModel aktualisiert: %d Eintraege", len(self.items))
        return list(self.items)


@dataclass
class PairsModel:
    items: list[PairRecord] = field(default_factory=list)

    def set_items(self, pairs: list[PairRecord]) -> list[PairRecord]:
        if not all(isinstance(pair, PairRecord) for pair in pairs):
            raise TypeError("PairsModel erwartet PairRecord-Einträge.")
        self.items = list(pairs)
        LOGGER.debug("PairsModel aktualisiert: %d Paare", len(self.items))
        return list(self.items)
