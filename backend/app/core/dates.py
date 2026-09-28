"""Date parsing helpers shared across providers and services.

Resumes contain dates in many shapes ("Mar 2021", "2021-03", "03/2021",
"2019 – Present"). These helpers are deterministic, best-effort and total:
unparseable input returns ``None`` rather than raising.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date
from typing import Protocol

_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

_ISO_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_ISO_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_YEAR_ONLY = re.compile(r"^(\d{4})$")
_MONTH_YEAR = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{4})$")
_SLASH = re.compile(r"^(\d{1,2})/(\d{4})$")


def parse_partial_date(value: object) -> date | None:
    """Best-effort parse of a resume-style date into a ``date``.

    Day precision is normalized to the first of the period (month → day 1,
    year → January 1st) — good enough for experience alignment.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    if match := _ISO_DAY.match(text):
        year, month, day = (int(part) for part in match.groups())
        return _safe_date(year, month, day)
    if match := _ISO_MONTH.match(text):
        year, month = (int(part) for part in match.groups())
        return _safe_date(year, month, 1)
    if match := _YEAR_ONLY.match(text):
        return _safe_date(int(match.group(1)), 1, 1)
    if match := _MONTH_YEAR.match(text):
        month = _MONTHS.get(match.group(1)[:3].lower())
        if month:
            return _safe_date(int(match.group(2)), month, 1)
    if match := _SLASH.match(text):
        month, year = (int(part) for part in match.groups())
        return _safe_date(year, month, 1)
    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


class _DatedExperience(Protocol):  # pragma: no cover - typing helper
    start_date: date | None
    end_date: date | None
    is_current: bool


def compute_years_experience(
    experiences: Iterable[_DatedExperience], *, today: date | None = None
) -> float | None:
    """Total professional years across dated roles, overlaps counted once."""
    today = today or date.today()
    ranges: list[tuple[date, date]] = []
    for experience in experiences:
        start = experience.start_date
        end = experience.end_date
        if experience.is_current or end is None:
            end = today
        if start and end and end >= start:
            ranges.append((start, end))
    if not ranges:
        return None

    ranges.sort()
    merged: list[list[date]] = [[ranges[0][0], ranges[0][1]]]
    for start, end in ranges[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / 365.25, 1)
