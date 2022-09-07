import logging

import discord
from discord.ext import commands

from .data import users


EMBED_COLOR = 0x8906A9
logger = logging.getLogger("discord")


async def save_and_message_ctx(
    ctx: commands.Context,
    message: str,
    title: str | None = None,
    mention: str | None = None,
) -> None:
    users.save()
    embed = discord.Embed(title=title, description=message, color=EMBED_COLOR)
    await ctx.send(content=mention, embed=embed)


async def save_and_message_guild(
    guild: discord.Guild,
    message: str,
    title: str | None = None,
    mention: str | None = None,
) -> None:
    users.save()
    embed = discord.Embed(title=title, description=message, color=EMBED_COLOR)
    for channel in guild.text_channels:
        try:
            await channel.send(content=mention, embed=embed)
            return
        except discord.errors.Forbidden:
            continue
    logger.warn(
        f"Unable to find a channel in guild#{guild.id} with permissions to send message"
    )
