from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import unique, IntEnum

timezone_to_utc_offset: dict[str, int] = {
    "HST": -10,
    "HDT": -9,
    "AKST": -9,
    "AKDT": -8,
    "PST": -8,
    "PDT": -7,
    "MST": -7,
    "MDT": -6,
    "CST": -6,
    "CDT": -5,
    "EST": -5,
    "EDT": -4,
}


@unique
class Repetition(IntEnum):
    DAILY = 0
    WEEKLY = 1


@unique
class Weekday(IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Recurrence:
    def __init__(self, repetition: Repetition, weekdays: list[Weekday] = []):
        self.repetition = repetition
        self.weekdays = weekdays

    def next_occurence(self, dt: datetime) -> datetime:
        dt.month
        repetition_to_num_days = {
            Repetition.DAILY: 1,
            Repetition.WEEKLY: days_until_valid_weekday(dt, self.weekdays),
        }
        return dt + timedelta(days=repetition_to_num_days[self.repetition])


@dataclass
class Commitment:
    owner_id: int
    name: str
    description: str
    next_check_in: datetime
    recurrence: Recurrence
    num_missed_in_a_row: int


@dataclass
class AccountabilityMember:
    user_id: int
    commitments: list[Commitment]
    is_active: bool
    timezone: str


def days_until_valid_weekday(dt: datetime, valid_weekdays: list[Weekday]) -> int:
    if not valid_weekdays:
        return -1
    current_weekday = dt.weekday()
    days = 1
    while (current_weekday := (current_weekday + 1) % 7) not in valid_weekdays:
        days += 1
    return days
