from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


class PairLike(Protocol):
    image_path: str
    audio_path: str | None
    output: str


@dataclass(frozen=True)
class MiniPreviewSummary:
    total_rows: int
    ready_rows: int
    conflict_rows: tuple[int, ...]
    lines: tuple[str, ...]


def build_mini_preview_summary(
    pairs: Sequence[PairLike],
    out_dir: str,
    *,
    max_lines: int = 3,
) -> MiniPreviewSummary:
    safe_max_lines = max(1, int(max_lines))
    normalized_out_dir = Path(out_dir).expanduser() if out_dir else None

    conflicts: list[int] = []
    lines: list[str] = []
    used_outputs: dict[str, int] = {}

    for index, pair in enumerate(pairs):
        row = index + 1
        missing = []
        if not (pair.image_path or "").strip():
            missing.append("Bild")
        if not (pair.audio_path or "").strip():
            missing.append("Audio")
        if missing:
            conflicts.append(index)
            lines.append(f"Zeile {row}: fehlt {', '.join(missing)}")
            continue

        output_value = (pair.output or "").strip()
        if output_value:
            output_path = Path(output_value)
        else:
            base_name = Path(str(pair.audio_path)).stem or f"paar_{row}"
            file_name = f"{base_name}.mp4"
            output_path = (
                normalized_out_dir / file_name
                if normalized_out_dir is not None
                else Path(file_name)
            )

        output_key = str(output_path)
        if output_key in used_outputs:
            conflicts.append(index)
            original_row = used_outputs[output_key] + 1
            lines.append(
                f"Zeile {row}: Konflikt, Ausgabe doppelt mit Zeile {original_row}"
            )
            continue
        used_outputs[output_key] = index
        lines.append(
            "Zeile "
            f"{row}: {Path(pair.image_path).name} + "
            f"{Path(str(pair.audio_path)).name} -> {output_path.name}"
        )

    ready_rows = max(0, len(pairs) - len(set(conflicts)))
    return MiniPreviewSummary(
        total_rows=len(pairs),
        ready_rows=ready_rows,
        conflict_rows=tuple(dict.fromkeys(conflicts)),
        lines=tuple(lines[:safe_max_lines]),
    )

