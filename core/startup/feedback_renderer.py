from __future__ import annotations

from typing import Iterable

from core import launcher_checks


def render_feedback(results: Iterable[launcher_checks.CheckResult]) -> str:
    feedback = launcher_checks.build_check_feedback(results)
    lines = [f"🧾 {feedback['headline']} | {feedback['summary']}"]
    for step in feedback.get("next_steps", []):
        lines.append(f"👉 {step}")
    for term in feedback.get("beginner_terms", []):
        lines.append(f"📘 {term}")
    for command in feedback.get("quick_commands", []):
        lines.append(f"⚙️ {command}")
    return "\n".join(lines)
