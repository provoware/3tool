from __future__ import annotations

import logging
from typing import Iterable, TypeVar

from .models import CheckFeedback, CheckResult, RepairFeedback, RepairResult

LOGGER = logging.getLogger("videobatch_launcher")
TResult = TypeVar("TResult", CheckResult, RepairResult)


def beginner_recovery_hints(results: Iterable[RepairResult]) -> list[str]:
    result_list = list(results)
    hints: list[str] = []
    failed = {item.key for item in result_list if not item.ok}
    if "dependency_files" in failed:
        hints.append(
            "Die Abhaengigkeitsdateien konnten nicht automatisch repariert "
            "werden. Bitte Schreibrechte pruefen und den Reparatur-Button "
            "erneut starten."
        )
    if "pip" in failed or "packages" in failed:
        hints.append(
            "Python-Pakete konnten nicht vollstaendig installiert werden. "
            "Bitte Internet, Rechte und danach den Button 'Reparieren' "
            "noch einmal pruefen."
        )
    if "ffmpeg" in failed:
        hints.append(
            "Video-Werkzeuge fehlen noch. Nutzen Sie den angezeigten "
            "Befehl fuer Ihr System (Paketmanager = Software-Verwalter)."
        )
    if "write_permissions" in failed:
        hints.append(
            "Es fehlen Schreibrechte im Projektordner. Starten Sie das Tool "
            "in einem eigenen Benutzerordner oder passen Sie Rechte an."
        )
    if any(item.skipped_offline for item in result_list):
        hints.append(
            "Offline erkannt: Nach Verbindungsaufbau bitte Reparatur erneut "
            "starten, damit fehlende Pakete automatisch nachinstalliert "
            "werden."
        )
    return hints


def _validated_results(
    results: Iterable[TResult], *, expected_type: type[TResult]
) -> list[TResult]:
    if not isinstance(results, Iterable):
        raise TypeError("results muss iterierbar sein.")
    result_list = list(results)
    if any(not isinstance(item, expected_type) for item in result_list):
        raise TypeError("results enthaelt unerwartete Ergebnistypen.")
    return result_list


def build_check_feedback(results: Iterable[CheckResult]) -> CheckFeedback:
    check_results = _validated_results(results, expected_type=CheckResult)
    blocking_total = sum(1 for item in check_results if item.blocking)
    blocking_ok = sum(1 for item in check_results if item.blocking and item.ok)
    optional_failed = [
        item.title
        for item in check_results
        if not item.blocking and not item.ok
    ]
    blocking_failed = [
        item.title for item in check_results if item.blocking and not item.ok
    ]
    failed_fix_hints = [
        item.fix_hint for item in check_results if not item.ok and item.fix_hint
    ]

    headline = (
        "Start bereit." if not blocking_failed else "Start noch nicht bereit."
    )
    next_steps: list[str] = []
    if blocking_failed:
        next_steps.append(
            "Bitte auf 'Reparieren' klicken, damit die Pflicht-Pruefungen "
            "automatisch behoben werden."
        )
    if optional_failed:
        next_steps.append(
            "Hinweis: Optionale Punkte sind offen (z. B. Internet). Das Tool "
            "kann meist trotzdem starten."
        )
    if not next_steps:
        next_steps.append(
            "Alle Pflichtpunkte sind grün. Sie können jetzt mit 'Starten' "
            "fortfahren."
        )

    quick_commands: list[str] = []
    for hint in failed_fix_hints:
        if isinstance(hint, str) and hint.startswith("Befehl:"):
            quick_commands.append(hint.removeprefix("Befehl:").strip())

    summary = (
        f"Pflichtpruefungen erfolgreich: {blocking_ok}/{max(blocking_total, 1)}"
    )
    LOGGER.info("Check-Feedback erstellt: %s | %s", headline, summary)
    return {
        "headline": headline,
        "summary": summary,
        "next_steps": next_steps,
        "beginner_terms": [
            "venv (virtuelle Umgebung): geschützter Python-Bereich nur für dieses Tool.",
            "pip (Paketmanager): installiert fehlende Python-Bausteine.",
            "ffmpeg: Werkzeug zum Verarbeiten von Video und Audio.",
            "Debug-Log: detailliertes Protokoll für die Fehlersuche.",
        ],
        "quick_commands": quick_commands,
    }


def build_repair_feedback(results: Iterable[RepairResult]) -> RepairFeedback:
    repair_results = _validated_results(results, expected_type=RepairResult)
    failed = [item.title for item in repair_results if not item.ok]
    offline_skips = sum(1 for item in repair_results if item.skipped_offline)
    hints = beginner_recovery_hints(repair_results)

    headline = "Reparatur erfolgreich abgeschlossen."
    if failed:
        headline = "Reparatur abgeschlossen, aber weitere Schritte noetig."

    summary = (
        f"Erfolgreich: {sum(1 for item in repair_results if item.ok)}/"
        f"{len(repair_results)}"
    )
    if offline_skips:
        summary += f" | Offline uebersprungen: {offline_skips}"

    LOGGER.info("Reparatur-Feedback erstellt: %s | %s", headline, summary)
    return {"headline": headline, "summary": summary, "hints": hints}
