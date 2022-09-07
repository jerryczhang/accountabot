from datetime import datetime

import discord
from discord.ext import commands, tasks  # type: ignore

from .commands import Accountability
from .data import User, users, user_time
from .message import save_and_message_ctx, save_and_message_guild


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="&", intents=intents)


@bot.event
async def on_ready():
    users.load()
    await bot.add_cog(Accountability(bot))
    activity = discord.Activity(
        type=discord.ActivityType.listening, name=f"{bot.command_prefix}help"
    )
    await bot.change_presence(activity=activity)

    _commitment_check_loop.start()


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    redirected_errors = [
        commands.errors.CommandNotFound,
        commands.errors.MissingRequiredArgument,
        commands.errors.UserInputError,
        commands.errors.UserNotFound,
    ]
    if type(error) in redirected_errors:
        await save_and_message_ctx(ctx, str(error))
    else:
        raise error


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


async def _check_commitment_check_ins_of_user(guild: discord.Guild, user: User) -> None:
    now = datetime.now().utcnow()
    user_now = user_time(user, now)
    for commitment in user.commitments:
        if user_now < commitment.next_check_in:
            continue
        commitment.cycle_check_in(missed=True)
        await save_and_message_guild(
            guild=guild,
            message=f"<@{user.member_id}> missed accountability commitment: {commitment}",
            title="Missed commitment",
            mention="@everyone",
        )
    users.save()


async def _check_commitment_reminders_of_user(guild: discord.Guild, user: User) -> None:
    now = datetime.now().utcnow()
    user_now = user_time(user, now)
    for commitment in user.commitments:
        reminder = commitment.reminder
        if (
            reminder is None
            or user_now.hour != reminder.hour
            or user_now.minute != reminder.minute
            or user_now.date() != commitment.next_check_in.date()
        ):
            continue
        await save_and_message_guild(
            guild=guild,
            message=str(commitment),
            title="Reminder",
            mention=f"<@{user.member_id}>",
        )
