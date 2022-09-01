from dataclasses import dataclass
from datetime import datetime, timedelta
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
    num_missed_in_a_row: int

    def cycle_check_in(self) -> None:
        self.next_check_in = self.recurrence.next_occurence(self.next_check_in)

    def __str__(self) -> str:
        output_list = [
            f"\n{self.name}:",
            f"\tDescription: {self.description}",
            f"\tNext check in: {self.next_check_in.strftime('%a, %b %d')}",
            f"\tNumber of misses in a row: {self.num_missed_in_a_row}",
            f"\tRepeats {self.recurrence}",
        ]
        return "\n".join(output_list)


@dataclass
class User:
    member_id: int
    commitments: list[Commitment]
    is_active: bool
    timezone: str

    def __str__(self) -> str:
        active = "Active" if self.is_active else "Inactive"
        if self.commitments:
            commitments = "\n".join(
                [str(commitment) for commitment in self.commitments]
            )
        else:
            commitments = "\nNo commitments"
        output_list = [
            f"<@{self.member_id}> [{active}] (Timezone: {self.timezone})\n",
            "".rjust(50, "-"),
            f"{commitments}",
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


def parse_recurrence(recurrence_str: str) -> Recurrence:
    recurrence_str = recurrence_str.lower()
    if "daily" in recurrence_str:
        return Recurrence(Repetition.DAILY)
    elif "weekly" in recurrence_str:
        weekdays = []
        for abv, weekday in _abbreviation_to_weekday.items():
            if abv in recurrence_str:
                weekdays.append(weekday)
        if not weekdays:
            raise ValueError(
                'Weekdays must be specified in a weekly occurence, e.g. "Sun", "Mon", "Tue", etc.'
            )
        return Recurrence(Repetition.WEEKLY, weekdays)
    else:
        raise ValueError('"daily" or "weekly" must be specified in recurrence')


def user_time(user: User, dt: datetime):
    return dt + timedelta(hours=_timezone_to_utc_offset[user.timezone])


_timezone_to_utc_offset: dict[str, int] = {
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

supported_timezones: list[str] = list(_timezone_to_utc_offset.keys())

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
