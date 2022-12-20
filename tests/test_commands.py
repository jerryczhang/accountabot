import pytest
from discord import Interaction

from accountabot import commands
from accountabot.commands import register
from accountabot.data import Timezone


@pytest.mark.asyncio
async def test_register_new_user(
    interaction_with_unregistered_user: Interaction,
):
    member_id = interaction_with_unregistered_user.user.id
    users = commands.users
    previous_num_users = len(users.member_id_to_user)
    await register.callback(interaction_with_unregistered_user, Timezone.MST)

    assert member_id in users.member_id_to_user
    assert users.member_id_to_user[member_id].timezone == Timezone.MST
    assert len(users.member_id_to_user) == previous_num_users + 1


@pytest.mark.asyncio
async def test_register_existing_user(interaction: Interaction):
    member_id = interaction.user.id
    users = commands.users
    previous_num_users = len(users.member_id_to_user)
    previous_commitment = users.member_id_to_user[member_id].commitment
    await register.callback(interaction, Timezone.MST)

    assert member_id in users.member_id_to_user
    assert users.member_id_to_user[member_id].timezone == Timezone.MST
    assert len(users.member_id_to_user) == previous_num_users
    assert previous_commitment == users.member_id_to_user[member_id].commitment
