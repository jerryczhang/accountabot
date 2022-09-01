import asyncio
from datetime import datetime, timedelta
import os

import discord
from discord.ext import commands, tasks  # type: ignore
from dotenv import load_dotenv

from .commands import Accountability, NotRegisteredError
from .data import User, users, timezone_to_utc_offset


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

    await _wait_until_next_hour()
    _commitment_check_loop.start()


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    redirected_errors = [
        commands.errors.CommandNotFound,
        commands.errors.MissingRequiredArgument,
        NotRegisteredError,
    ]
    if type(error) in redirected_errors:
        await ctx.send(error)
    else:
        raise error


@tasks.loop(hours=1)
async def _commitment_check_loop():
    for guild in bot.guilds:
        for member in guild.members:
            if member.id not in users.member_id_to_user:
                continue
            user = users.member_id_to_user[member.id]
            await _check_commitments_of_user(guild, user)
    users.save()


async def _wait_until_next_hour() -> None:
    now = datetime.now()
    next_hour = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour + 1,
    )
    await asyncio.sleep((next_hour - datetime.now()).total_seconds())


async def _send_message_to_guild(guild: discord.Guild, message: str) -> None:
    for channel in guild.text_channels:
        try:
            await channel.send(message)
            return
        except discord.errors.Forbidden:
            continue
    raise RuntimeError(
        f"Unable to find a channel in guild#{guild.id} with permissions to send message"
    )


async def _check_commitments_of_user(guild: discord.Guild, user: User) -> None:
    now = datetime.now().utcnow()
    user_time = now + timedelta(hours=timezone_to_utc_offset[user.timezone])
    for commitment in user.commitments:
        if user_time < commitment.next_check_in:
            continue
        commitment.num_missed_in_a_row += 1
        await _send_message_to_guild(
            guild, f"@<{user.member_id}> missed accountability commitment: {commitment}"
        )
        commitment.next_check_in = commitment.recurrence.next_occurence(
            commitment.next_check_in
        )


if __name__ == "__main__":
    load_dotenv()

    bot.run(os.getenv("DISCORD_TOKEN"))
