import asyncio
from datetime import datetime, timedelta
import os
import pickle

import discord
from discord.ext import commands, tasks  # type: ignore
from dotenv import load_dotenv

from .data import Commitment, AccountabilityMember, Recurrence, timezone_to_utc_offset


MEMBERS_FILE = "members.pkl"


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


async def check_commitments_of_member(
    guild: discord.Guild, member: AccountabilityMember
) -> None:
    now = datetime.now().utcnow()
    member_time = now + timedelta(hours=timezone_to_utc_offset[member.timezone])
    for commitment in member.commitments:
        if member_time < commitment.next_check_in:
            continue
        commitment.num_missed_in_a_row += 1
        await send_message_to_guild(
            guild, f"@<{member.user_id}> failed accountability commitment: {commitment}"
        )
        commitment.next_check_in = commitment.recurrence.next_occurence(
            commitment.next_check_in
        )


class Accountabot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.members: dict[discord.Member, AccountabilityMember] = {}

    def save(self, fname: str) -> None:
        with open(fname, "wb") as f:
            pickle.dump(self.members, f)

    def load(self, fname: str) -> None:
        with open(fname, "rb") as f:
            self.members = pickle.load(f)


class Accountability(commands.Cog):
    """Commands to manage your accountability commitments"""

    def __init__(self, bot: Accountabot):
        self.bot = bot

    @commands.command()
    async def register(self, ctx: commands.Context, timezone: str):
        """Register yourself as a new user"""
        timezone = timezone.upper()
        if timezone not in timezone_to_utc_offset:
            invalid_timezone_message = (
                f"Timezone '{timezone}' isn't valid\n"
                f"Supported timezones: {', '.join(list(timezone_to_utc_offset.keys()))}"
            )
            await ctx.send(invalid_timezone_message)
            return

        member = ctx.author
        if member in self.bot.members:
            self.bot.members[member].timezone = timezone
            await ctx.send(f"User successfully updated:\n{self.bot.members[member]}")
        else:
            new_member = AccountabilityMember(
                user_id=member.id, commitments=[], is_active=True, timezone=timezone
            )
            self.bot.members[member] = new_member
            await ctx.send(f"Registration successful!\n{new_member}")


bot = Accountabot(command_prefix="&", intents=intents)


@tasks.loop(hours=1)
async def commitment_check_loop():
    for guild in bot.guilds:
        members = guild.members
        for member in members:
            if member not in bot.members:
                continue
            await check_commitments_of_member(guild, member)
    bot.save(MEMBERS_FILE)


@bot.event
async def on_ready():
    if os.path.exists(MEMBERS_FILE):
        bot.load(MEMBERS_FILE)
    await bot.add_cog(Accountability(bot))
    await wait_until_next_hour()
    commitment_check_loop.start()


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    error_type_to_message = {
        commands.errors.CommandNotFound: error,
        commands.errors.MissingRequiredArgument: f"{ctx.command.name}: {error}",
    }
    error_type = type(error)
    if error_type in error_type_to_message:
        await ctx.send(error_type_to_message[error_type])
    else:
        raise error


if __name__ == "__main__":
    load_dotenv()

    bot.run(os.getenv("DISCORD_TOKEN"))
