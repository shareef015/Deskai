from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class BusinessCalendar:
    timezone: str
    workday_start: time
    workday_end: time
    working_weekdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})
    holidays: frozenset[date] = frozenset()

    def add_minutes(self, start: datetime, minutes: int) -> datetime:
        if start.tzinfo is None or minutes < 0:
            raise ValueError("aware start time and nonnegative minutes are required")
        zone = ZoneInfo(self.timezone)
        cursor = start.astimezone(zone)
        remaining = minutes
        while remaining:
            if cursor.weekday() not in self.working_weekdays or cursor.date() in self.holidays:
                cursor = datetime.combine(cursor.date() + timedelta(days=1), self.workday_start, zone)
                continue
            opening = datetime.combine(cursor.date(), self.workday_start, zone)
            closing = datetime.combine(cursor.date(), self.workday_end, zone)
            cursor = max(cursor, opening)
            if cursor >= closing:
                cursor = datetime.combine(cursor.date() + timedelta(days=1), self.workday_start, zone)
                continue
            available = int((closing - cursor).total_seconds() // 60)
            consumed = min(remaining, available)
            cursor += timedelta(minutes=consumed)
            remaining -= consumed
        return cursor.astimezone(start.tzinfo)
