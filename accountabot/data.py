from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import unique, IntEnum
import os
import pickle


USERS_FILE = "users.pkl"


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


@unique
class Timezone(IntEnum):
    HST = -10
    AKST = -9
    PST = -8
    MST = -7
    CST = -6
    EST = -5


@dataclass
class Recurrence:
    def __init__(self, repetition: Repetition, weekdays: list[Weekday] = []):
        self.repetition = repetition
        self.weekdays = weekdays

    def next_occurence(self, dt: datetime) -> datetime:
        dt.month
        repetition_to_num_days = {
            Repetition.DAILY: 1,
            Repetition.WEEKLY: _days_until_valid_weekday(dt, self.weekdays),
        }
        return dt + timedelta(days=repetition_to_num_days[self.repetition])

    @classmethod
    def from_str(cls, value: str) -> Recurrence:
        recurrence_str = value.lower()
        if "daily" in recurrence_str:
            return cls(Repetition.DAILY)
        elif "weekly" in recurrence_str:
            weekdays = []
            for abv, weekday in _abbreviation_to_weekday.items():
                if abv in recurrence_str:
                    weekdays.append(weekday)
            if not weekdays:
                raise ValueError(
                    "Weekdays must be specified in a weekly occurence, e.g. 'Sun', 'Mon', 'Tue', etc."
                )
            return cls(Repetition.WEEKLY, weekdays)
        else:
            raise ValueError("'daily' or 'weekly' must be specified in recurrence")

    def __str__(self) -> str:
        if self.repetition == Repetition.DAILY:
            return "daily"
        else:
            weekdays = ", ".join(weekday.name.title() for weekday in self.weekdays)
            return f"weekly on {weekdays}"


@dataclass
class Commitment:
    owner_id: int
    name: str
    description: str
    next_check_in: datetime
    recurrence: Recurrence
    streak: int
    num_missed_in_a_row: int
    reminder: time | None

    def cycle_check_in(self, missed: bool) -> None:
        if missed:
            self.streak = 0
            self.num_missed_in_a_row += 1
        else:
            self.streak += 1
            self.num_missed_in_a_row = 0
        self.next_check_in = self.recurrence.next_occurence(self.next_check_in)

    def __str__(self) -> str:
        output_list = [
            f"{self.name}:",
            f"\tDescription: {self.description}",
            f"\tNext check in: {self.next_check_in.strftime('%a, %b %d')}",
            f"\tReminder: {self.reminder.strftime('%I:%M %p') if self.reminder else None}",
            f"\tStreak: {self.streak}",
            f"\tNumber of misses in a row: {self.num_missed_in_a_row}",
            f"\tRepeats {self.recurrence}",
        ]
        return "\n".join(output_list)


@dataclass
class User:
    member_id: int
    commitment: Commitment | None
    is_active: bool
    timezone: Timezone

    def __str__(self) -> str:
        active = "Active" if self.is_active else "Inactive"
        output_list = [
            f"<@{self.member_id}> [{active}] (Timezone: {self.timezone.name})\n",
            "\n".rjust(50, "-"),
            "No commitment" if self.commitment is None else str(self.commitment),
        ]
        return "".join(output_list)


@dataclass
class Users:
    member_id_to_user: dict[int, User]

    def save(self) -> None:
        with open(USERS_FILE, "wb") as f:
            pickle.dump(self.member_id_to_user, f)

    def load(self) -> None:
        if not os.path.exists(USERS_FILE):
            return
        with open(USERS_FILE, "rb") as f:
            self.member_id_to_user = pickle.load(f)


users = Users(member_id_to_user={})


def user_time(user: User, dt: datetime):
    return dt + timedelta(hours=user.timezone.value)


_abbreviation_to_weekday: dict[str, Weekday] = {
    "mon": Weekday.MONDAY,
    "tue": Weekday.TUESDAY,
    "wed": Weekday.WEDNESDAY,
    "thu": Weekday.THURSDAY,
    "fri": Weekday.FRIDAY,
    "sat": Weekday.SATURDAY,
    "sun": Weekday.SUNDAY,
}


def _days_until_valid_weekday(dt: datetime, valid_weekdays: list[Weekday]) -> int:
    if not valid_weekdays:
        return -1
    current_weekday = dt.weekday()
    days = 1
    while (current_weekday := (current_weekday + 1) % 7) not in valid_weekdays:
        days += 1
    return days
