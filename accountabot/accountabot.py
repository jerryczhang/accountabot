import logging
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import tasks  # type: ignore
from dotenv import load_dotenv

from .data import User
from .data import user_time
from .data import users
from .message import save_and_message_guild


bot = discord.Client(intents=discord.Intents.all())
command_tree = app_commands.CommandTree(bot)
logger = logging.getLogger("discord")


def main() -> int:
    load_dotenv()
    bot.run(os.getenv("DISCORD_TOKEN"))


@bot.event
async def on_ready():
    for guild in bot.guilds:
        command_tree.copy_global_to(guild=guild)
        await command_tree.sync(guild=guild)

    users.load()
    logger.info("Users loaded")
    _commitment_check_loop.start()


@tasks.loop(minutes=1)
async def _commitment_check_loop():
    for guild in bot.guilds:
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
    now = datetime.now().utcnow()
    user_now = user_time(user, now)
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
    users.save()


async def _check_commitment_reminders_of_user(
    guild: discord.Guild, user: User
) -> None:
    now = datetime.now().utcnow()
    user_now = user_time(user, now)
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
