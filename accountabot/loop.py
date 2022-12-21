from datetime import datetime

import discord
from discord.ext import tasks

from .data import get_users
from .data import User
from .data import user_time
from .message import save_and_message_guild


@tasks.loop(minutes=1)
async def commitment_check_loop(guilds: list[discord.Guild]):
    users = get_users()
    for guild in guilds:
        for member in guild.members:
            if member.id not in users.member_id_to_user:
                continue
            user = users.member_id_to_user[member.id]
            if not user.is_active:
                continue
            await _check_commitment_check_ins_of_user(guild, user)
            await _check_commitment_reminders_of_user(guild, user)
    users.save()


async def _check_commitment_check_ins_of_user(
    guild: discord.Guild, user: User
) -> None:
    user_now = user_time(user, datetime.utcnow())
    commitment = user.commitment
    if commitment is None or user_now < commitment.next_check_in:
        return
    commitment.cycle_check_in(missed=True)
    await save_and_message_guild(
        guild=guild,
        message=f"<@{user.member_id}> missed accountability commitment: \n{commitment}",
        title="Missed commitment",
        mention="@everyone",
    )


async def _check_commitment_reminders_of_user(
    guild: discord.Guild, user: User
) -> None:
    user_now = user_time(user, datetime.utcnow())
    commitment = user.commitment
    if commitment is None:
        return
    reminder = commitment.reminder
    if (
        reminder is None
        or user_now.hour != reminder.hour
        or user_now.minute != reminder.minute
        or user_now.date() != commitment.next_check_in.date()
    ):
        return
    await save_and_message_guild(
        guild=guild,
        message=str(commitment),
        title="Reminder",
        mention=f"<@{user.member_id}>",
    )
