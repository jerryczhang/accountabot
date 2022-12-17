from datetime import datetime
from datetime import time
from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands

from .accountabot import command_tree
from .data import Commitment
from .data import Recurrence
from .data import Timezone
from .data import User
from .data import user_time
from .data import users
from .message import save_and_message_interaction


def _is_registered(interaction: discord.Interaction) -> bool:
    is_registered = interaction.user.id in users.member_id_to_user
    if not is_registered:
        raise app_commands.AppCommandError(
            "Use the 'register' command to register yourself as a user first!"
        )
    return True


def _has_commitment(interaction: discord.Interaction) -> bool:
    user = users.member_id_to_user[interaction.user.id]
    if user.commitment is None:
        raise app_commands.AppCommandError(
            "Use the 'commit' command to create an accountability commitment first!"
        )
    return True


class _TimeTransformer(app_commands.Transformer):
    async def transform(self, _: discord.Interaction, value: str) -> time:
        try:
            return datetime.strptime(value.upper(), "%I:%M %p").time()
        except ValueError:
            raise app_commands.AppCommandError(
                f"Cannot parse time '{value}', make sure to use format 'H:MM AM/PM'"
            )


class _RecurrenceTransformer(app_commands.Transformer):
    async def transform(self, _: discord.Interaction, value: str) -> Recurrence:
        try:
            return Recurrence.from_str(value)
        except ValueError as ex:
            raise app_commands.AppCommandError(ex)


@command_tree.error
async def on_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    await save_and_message_interaction(interaction, str(error), ephemeral=True)


@command_tree.command()
@app_commands.describe(timezone="Your timezone")
async def register(interaction: discord.Interaction, timezone: Timezone):
    """Register yourself as a new user, or update your existing profile"""

    member_id = interaction.user.id
    if member_id in users.member_id_to_user:
        user = users.member_id_to_user[member_id]
        user.timezone = timezone
        await save_and_message_interaction(
            interaction, str(user), title="User Updated"
        )
    else:
        new_user = User(
            member_id=member_id,
            commitment=None,
            is_active=True,
            timezone=timezone,
        )
        users.member_id_to_user[member_id] = new_user
        await save_and_message_interaction(
            interaction, str(new_user), title="Registered!"
        )


@command_tree.command()
@app_commands.describe(
    name="What do you want to commit to?",
    description="A brief description of your commitment",
    recurrence="How often you want your commitment to repeat",
    reminder="When to be reminded about your commitment (in format HH:MM AM/PM)",
)
@app_commands.check(_is_registered)
async def commit(
    interaction: discord.Interaction,
    name: str,
    description: str,
    recurrence: app_commands.Transform[Recurrence, _RecurrenceTransformer],
    reminder: Optional[app_commands.Transform[time, _TimeTransformer]],
):
    """Create a new commitment, or update existing commitment by name"""

    user = users.member_id_to_user[interaction.user.id]
    commitment = user.commitment
    if commitment:
        commitment.name = name
        commitment.description = description
        commitment.recurrence = recurrence
        commitment.reminder = reminder
        await save_and_message_interaction(
            interaction, str(commitment), title="Commitment updated"
        )
    else:
        user.commitment = Commitment(
            owner_id=user.member_id,
            name=name,
            description=description,
            next_check_in=_first_check_in(user, recurrence),
            recurrence=recurrence,
            streak=0,
            num_missed_in_a_row=0,
            reminder=reminder,
        )
        await save_and_message_interaction(
            interaction, str(user.commitment), title="Commitment created!"
        )


@command_tree.command()
@app_commands.check(_has_commitment)
@app_commands.check(_is_registered)
async def check(interaction: discord.Interaction):
    """Check in your accountability commitment (mark as completed)"""

    user = users.member_id_to_user[interaction.user.id]
    commitment = user.commitment
    time_until_commitment = commitment.next_check_in - user_time(
        user, datetime.now()
    )
    if time_until_commitment.days >= 1:
        raise app_commands.AppCommandError(
            "You aren't supposed to do this commitment yet! "
            f"Next check in is in {time_until_commitment.days} more day(s)"
        )

    commitment.cycle_check_in(missed=False)
    await save_and_message_interaction(
        interaction, str(commitment), title="Checked in!"
    )

    if commitment.streak % 10 == 0:
        await save_and_message_interaction(
            interaction,
            f"<@{user.member_id}>: {commitment.name}",
            title=f"Streak of {commitment.streak} reached!",
            mention="@everyone",
        )


@command_tree.command()
@app_commands.check(_has_commitment)
@app_commands.check(_is_registered)
async def delete(interaction: discord.Interaction):
    """Delete an accountability commitment"""

    user = users.member_id_to_user[interaction.user.id]
    commitment = user.commitment
    user.commitment = None
    await save_and_message_interaction(
        interaction, str(commitment), title="Deleted commitment"
    )


@command_tree.command()
@app_commands.check(_has_commitment)
@app_commands.check(_is_registered)
@app_commands.describe(
    reminder="When to be reminded about your commitment (in format HH:MM AM/PM)"
)
async def remind(
    interaction: discord.Interaction,
    reminder: app_commands.Transform[time, _TimeTransformer],
):
    """Set up or remove a reminder"""

    commitment = users.member_id_to_user[interaction.user.id].commitment
    commitment.reminder = reminder
    await save_and_message_interaction(
        interaction, str(commitment), title="Commitment updated"
    )


@command_tree.command()
@app_commands.check(_is_registered)
async def info(interaction: discord.Interaction):
    """Display info about your profile and commitment"""

    user = users.member_id_to_user[interaction.user.id]
    await save_and_message_interaction(
        interaction, str(user), title="User info"
    )


@command_tree.command(name="toggle-active")
@app_commands.check(_is_registered)
async def toggle_active(interaction: discord.Interaction):
    """Toggles your profile between active and inactive"""

    user = users.member_id_to_user[interaction.user.id]
    user.is_active = not user.is_active
    if user.is_active:
        commitment = user.commitment
        commitment.next_check_in = _first_check_in(user, commitment.recurrence)
    await save_and_message_interaction(
        interaction, str(user), title="User activity updated"
    )


def _first_check_in(user: User, recurrence: Recurrence) -> datetime:
    now = user_time(user, datetime.now().utcnow())
    midnight = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=23,
        minute=59,
        second=59,
    )
    return recurrence.next_occurence(midnight - timedelta(days=1))
