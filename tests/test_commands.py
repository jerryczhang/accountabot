from datetime import time

import pytest
from discord import Interaction
from discord.app_commands.errors import AppCommandError

from accountabot.commands import check
from accountabot.commands import commit
from accountabot.commands import delete
from accountabot.commands import info
from accountabot.commands import register
from accountabot.commands import remind
from accountabot.commands import toggle_active
from accountabot.data import Recurrence
from accountabot.data import Repetition
from accountabot.data import Timezone
from accountabot.data import Users


@pytest.mark.asyncio
async def test_register_new_user(
    interaction_with_unregistered_user: Interaction, users: Users
):
    member_id = interaction_with_unregistered_user.user.id
    previous_num_users = len(users.member_id_to_user)
    await register.callback(interaction_with_unregistered_user, Timezone.MST)

    assert member_id in users.member_id_to_user
    assert users.member_id_to_user[member_id].timezone == Timezone.MST
    assert len(users.member_id_to_user) == previous_num_users + 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interaction",
    ["interaction_with_uncommitted_user", "interaction_with_committed_user"],
)
async def test_register_existing_user(
    interaction: Interaction, users: Users, request: pytest.FixtureRequest
):
    interaction = request.getfixturevalue(interaction)
    member_id = interaction.user.id
    previous_num_users = len(users.member_id_to_user)
    previous_commitment = users.member_id_to_user[member_id].commitment
    await register.callback(interaction, Timezone.MST)

    assert member_id in users.member_id_to_user
    assert users.member_id_to_user[member_id].timezone == Timezone.MST
    assert len(users.member_id_to_user) == previous_num_users
    assert previous_commitment == users.member_id_to_user[member_id].commitment


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interaction",
    ["interaction_with_uncommitted_user", "interaction_with_committed_user"],
)
async def test_commit(
    interaction: Interaction, users: Users, request: pytest.FixtureRequest
):
    interaction = request.getfixturevalue(interaction)
    await commit.callback(
        interaction,
        "Test commitment",
        "A test commitment",
        Recurrence(Repetition.DAILY),
        None,
    )
    commitment = users.member_id_to_user[interaction.user.id].commitment

    assert commitment.name == "Test commitment"
    assert commitment.description == "A test commitment"
    assert commitment.recurrence == Recurrence(Repetition.DAILY)


@pytest.mark.asyncio
async def test_check_throws_on_uncommitted_user(
    interaction_with_uncommitted_user: Interaction,
):
    with pytest.raises(AppCommandError) as ex:
        await check.callback(interaction_with_uncommitted_user)

    assert "commit" in str(ex.value)


@pytest.mark.asyncio
async def test_check(
    interaction_with_committed_user: Interaction, users: Users
):
    user = users.member_id_to_user[interaction_with_committed_user.user.id]
    previous_check_in = user.commitment.next_check_in
    await check.callback(interaction_with_committed_user)
    with pytest.raises(AppCommandError):
        await check.callback(interaction_with_committed_user)

    assert user.commitment.next_check_in > previous_check_in


@pytest.mark.asyncio
async def test_delete(
    interaction_with_committed_user: Interaction, users: Users
):
    user = users.member_id_to_user[interaction_with_committed_user.user.id]
    await delete.callback(interaction_with_committed_user)

    assert user.commitment is None


@pytest.mark.asyncio
async def test_remind(
    interaction_with_committed_user: Interaction, users: Users
):
    user = users.member_id_to_user[interaction_with_committed_user.user.id]
    reminder = time(10, 10, 10, 0)
    await remind.callback(interaction_with_committed_user, reminder)

    assert user.commitment.reminder == reminder


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interaction",
    ["interaction_with_uncommitted_user", "interaction_with_committed_user"],
)
async def test_info_sends_message(
    interaction: Interaction, request: pytest.FixtureRequest
):
    interaction = request.getfixturevalue(interaction)
    await info.callback(interaction)

    assert interaction.response.send_message.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interaction",
    ["interaction_with_uncommitted_user", "interaction_with_committed_user"],
)
async def test_toggle_active(
    interaction: Interaction, users: Users, request: pytest.FixtureRequest
):
    interaction = request.getfixturevalue(interaction)
    user = users.member_id_to_user[interaction.user.id]
    await toggle_active.callback(interaction)
    is_active_after_toggle = user.is_active
    await toggle_active.callback(interaction)

    assert not is_active_after_toggle
    assert user.is_active
