from __future__ import annotations

COLUMNS = [
    "#",
    "Thumb",
    "Bild",
    "Audio",
    "Dauer",
    "Ausgabe",
    "Fortschritt",
    "Status",
]


def table_columns() -> list[str]:
    return list(COLUMNS)
