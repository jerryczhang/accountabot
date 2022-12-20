from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from discord import Interaction

from accountabot.data import Commitment
from accountabot.data import get_users
from accountabot.data import Recurrence
from accountabot.data import Repetition
from accountabot.data import Timezone
from accountabot.data import User
from accountabot.data import Users


UNREGISTERED_USER_ID = 0
UNCOMMITED_USER_ID = 1
COMMITTED_USER_ID = 2


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
    return get_users()


@pytest.fixture(autouse=True)
def patch_users():
    commitment = Commitment(
        owner_id=COMMITTED_USER_ID,
        name="Test commitment",
        description="This is a test commitment",
        next_check_in=datetime.now(),
        recurrence=Recurrence(Repetition.DAILY),
        streak=0,
        num_missed_in_a_row=0,
        reminder=None,
    )
    committed_user = User(
        member_id=COMMITTED_USER_ID,
        commitment=commitment,
        is_active=True,
        timezone=Timezone.PST,
    )
    uncommitted_user = User(
        member_id=UNCOMMITED_USER_ID,
        commitment=None,
        is_active=True,
        timezone=Timezone.AKST,
    )
    users = Users(
        {
            COMMITTED_USER_ID: committed_user,
            UNCOMMITED_USER_ID: uncommitted_user,
        }
    )
    with patch("accountabot.data._users", users):
        yield


@pytest.fixture(autouse=True)
def patch_user_file(tmp_path):
    with patch("accountabot.data.USERS_FILE", tmp_path / "users.pkl"):
        yield
