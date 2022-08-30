from datetime import datetime

from accountabot.data import Recurrence
from accountabot.data import Repetition
from accountabot.data import Weekday


def test_daily_recurrence():
    r = Recurrence(Repetition.DAILY)

    assert r.next_occurence(datetime(2022, 8, 28)) == datetime(2022, 8, 29)
    assert r.next_occurence(datetime(2022, 9, 30)) == datetime(2022, 10, 1)
    assert r.next_occurence(datetime(2024, 2, 29)) == datetime(2024, 3, 1)
    assert r.next_occurence(datetime(2022, 12, 31)) == datetime(2023, 1, 1)


def test_weekly_recurrence():
    r_mwf = Recurrence(
        Repetition.WEEKLY, [Weekday.MONDAY, Weekday.WEDNESDAY, Weekday.FRIDAY]
    )

    # 8/29/2022 is a Monday
    assert r_mwf.next_occurence(datetime(2022, 8, 29)) == datetime(2022, 8, 31)
    assert r_mwf.next_occurence(datetime(2022, 8, 30)) == datetime(2022, 8, 31)
    assert r_mwf.next_occurence(datetime(2022, 8, 31)) == datetime(2022, 9, 2)
    # 12/31/2022 is a Saturday
    assert r_mwf.next_occurence(datetime(2022, 12, 31)) == datetime(2023, 1, 2)
    # 2/29/2024 is a Thursday
    assert r_mwf.next_occurence(datetime(2024, 2, 29)) == datetime(2024, 3, 1)
