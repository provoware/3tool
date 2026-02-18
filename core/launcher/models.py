from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


@dataclass(frozen=True)
class PackageManagerInfo:
    name: str
    update_cmd: list[str] | None
    install_cmd: list[str]


@dataclass(frozen=True)
class CheckResult:
    key: str
    title: str
    ok: bool
    detail: str
    fix_hint: str | None = None
    blocking: bool = True


@dataclass(frozen=True)
class RepairResult:
    key: str
    title: str
    ok: bool
    detail: str
    skipped_offline: bool = False


@dataclass(frozen=True)
class ReleaseReadinessResult:
    key: str
    title: str
    ok: bool
    detail: str
    recommendation: str
    blocking: bool = True


class CheckFeedback(TypedDict):
    headline: str
    summary: str
    next_steps: list[str]
    beginner_terms: list[str]
    quick_commands: list[str]


class RepairFeedback(TypedDict):
    headline: str
    summary: str
    hints: list[str]
