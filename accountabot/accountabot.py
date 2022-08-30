import asyncio
from datetime import datetime, timedelta
import os

import discord
from discord.ext import commands, tasks  # type: ignore
from dotenv import load_dotenv

from .commands import Accountability
from .data import User, users, timezone_to_utc_offset


intents = discord.Intents.all()


async def wait_until_next_hour() -> None:
    now = datetime.now()
    next_hour = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour + 1,
    )
    await asyncio.sleep((next_hour - datetime.now()).total_seconds())


async def send_message_to_guild(guild: discord.Guild, message: str) -> None:
    for channel in guild.text_channels:
        try:
            await channel.send(message)
            return
        except discord.errors.Forbidden:
            continue
    raise RuntimeError(
        f"Unable to find a channel in guild#{guild.id} with permissions to send message"
    )


async def check_commitments_of_user(guild: discord.Guild, user: User) -> None:
    now = datetime.now().utcnow()
    user_time = now + timedelta(hours=timezone_to_utc_offset[user.timezone])
    for commitment in user.commitments:
        if user_time < commitment.next_check_in:
            continue
        commitment.num_missed_in_a_row += 1
        await send_message_to_guild(
            guild, f"@<{user.member_id}> missed accountability commitment: {commitment}"
        )
        commitment.next_check_in = commitment.recurrence.next_occurence(
            commitment.next_check_in
        )


bot = commands.Bot(command_prefix="&", intents=intents)


@tasks.loop(hours=1)
async def commitment_check_loop():
    for guild in bot.guilds:
        for member in guild.members:
            if member.id not in users.member_id_to_user:
                continue
            user = users.member_id_to_user[member.id]
            await check_commitments_of_user(guild, user)
    users.save()


@bot.event
async def on_ready():
    users.load()
    await bot.add_cog(Accountability(bot))

    await wait_until_next_hour()
    commitment_check_loop.start()


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    error_type_to_message = {
        commands.errors.CommandNotFound: error,
        commands.errors.MissingRequiredArgument: error,
    }
    error_type = type(error)
    if error_type in error_type_to_message:
        await ctx.send(error_type_to_message[error_type])
    else:
        raise error


if __name__ == "__main__":
    load_dotenv()

    bot.run(os.getenv("DISCORD_TOKEN"))
