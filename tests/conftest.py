from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import discord
import pytest
from discord import Interaction

from accountabot.data import Commitment
from accountabot.data import Recurrence
from accountabot.data import Repetition
from accountabot.data import Timezone
from accountabot.data import User
from accountabot.data import user_time
from accountabot.data import Users


UNREGISTERED_USER_ID = 0
UNCOMMITED_USER_ID = 1
COMMITTED_USER_ID = 2
OVERDUE_COMMITED_USER_ID = 3


MOCK_DATETIME = datetime(2022, 12, 20, 5, 0, 0, 0)


class MockSendMessage(MagicMock):
    def __call__(self, *args, **kwargs):
        super().__call__(args, kwargs)

        async def mock_send_message():
            ...

        return mock_send_message()


@pytest.fixture
def _interaction():
    interaction = MagicMock(spec=Interaction)
    interaction.response.send_message = MockSendMessage()
    return interaction


@pytest.fixture
def interaction_with_unregistered_user(_interaction):
    _interaction.user.id = UNREGISTERED_USER_ID
    return _interaction


@pytest.fixture
def interaction_with_uncommitted_user(_interaction):
    _interaction.user.id = UNCOMMITED_USER_ID
    return _interaction


@pytest.fixture
def interaction_with_committed_user(_interaction):
    _interaction.user.id = COMMITTED_USER_ID
    return _interaction


@pytest.fixture
def users():
    users = MagicMock(
        spec=Users,
        member_id_to_user={
            COMMITTED_USER_ID: _get_user(committed=True),
            UNCOMMITED_USER_ID: _get_user(committed=False),
            OVERDUE_COMMITED_USER_ID: _get_user(committed=True, overdue=True),
        },
    )
    return users


@pytest.fixture
def guild():
    guild = MagicMock(spec=discord.Guild)
    guild.members = [
        MagicMock(spec=discord.Member, id=id)
        for id in [
            UNREGISTERED_USER_ID,
            UNCOMMITED_USER_ID,
            COMMITTED_USER_ID,
            OVERDUE_COMMITED_USER_ID,
        ]
    ]
    guild.text_channels = [
        MagicMock(spec=discord.TextChannel, send=MockSendMessage())
    ]

    return guild


@pytest.fixture(autouse=True)
def patch_users(users):
    with (
        patch("accountabot.commands.get_users") as commands_users,
        patch("accountabot.loop.get_users") as loop_users,
    ):
        commands_users.return_value = users
        loop_users.return_value = users
        yield


@pytest.fixture(autouse=True)
def patch_now():
    with (
        patch("accountabot.commands.datetime") as commands_dt,
        patch("accountabot.loop.datetime") as loop_dt,
    ):
        commands_dt.utcnow.return_value = MOCK_DATETIME
        loop_dt.utcnow.return_value = MOCK_DATETIME
        yield


def _get_user(committed: bool, overdue: bool = False):
    if not committed:
        member_id = UNCOMMITED_USER_ID
    elif overdue:
        member_id = OVERDUE_COMMITED_USER_ID
    else:
        member_id = COMMITTED_USER_ID
    check_in_offset = timedelta(seconds=-1) if overdue else timedelta(seconds=1)

    user = User(
        member_id=member_id,
        commitment=None,
        is_active=True,
        timezone=Timezone.PST,
    )
    user_now = user_time(user, MOCK_DATETIME)
    commitment = Commitment(
        owner_id=member_id,
        name="Test commitment",
        description="This is a test commitment",
        next_check_in=user_now + check_in_offset,
        recurrence=Recurrence(Repetition.DAILY),
        streak=0,
        num_missed_in_a_row=0,
        reminder=user_now.time(),
    )
    if committed:
        user.commitment = commitment

    return user
