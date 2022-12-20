from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from discord import Interaction

from accountabot.data import Commitment
from accountabot.data import Recurrence
from accountabot.data import Repetition
from accountabot.data import Timezone
from accountabot.data import User
from accountabot.data import Users


REGISTERED_USER_ID = 0
UNREGISTERED_USER_ID = 1


async def mock_send_message():
    ...


@pytest.fixture
def interaction():
    interaction = MagicMock(spec=Interaction)
    interaction.user.id = REGISTERED_USER_ID
    interaction.response.send_message.return_value = mock_send_message()

    return interaction


@pytest.fixture
def interaction_with_unregistered_user():
    interaction = MagicMock(spec=Interaction)
    interaction.user.id = UNREGISTERED_USER_ID
    interaction.response.send_message.return_value = mock_send_message()

    return interaction


@pytest.fixture(autouse=True)
def patch_users():
    commitment = Commitment(
        owner_id=REGISTERED_USER_ID,
        name="Test commitment",
        description="This is a test commitment",
        next_check_in=datetime.now(),
        recurrence=Recurrence(Repetition.DAILY),
        streak=0,
        num_missed_in_a_row=0,
        reminder=None,
    )
    user = User(
        member_id=REGISTERED_USER_ID,
        commitment=commitment,
        is_active=True,
        timezone=Timezone.PST,
    )
    users = Users({REGISTERED_USER_ID: user})
    with patch("accountabot.commands.users", users):
        yield


@pytest.fixture(autouse=True)
def patch_user_file(tmp_path):
    with patch("accountabot.data.USERS_FILE", tmp_path / "users.pkl"):
        yield
