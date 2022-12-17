import logging

import discord

from .data import users


EMBED_COLOR = 0x8906A9
logger = logging.getLogger("discord")


async def save_and_message_interaction(
    interaction: discord.Interaction,
    message: str,
    title: str | None = None,
    mention: str | None = None,
    ephemeral=False,
) -> None:
    users.save()
    embed = discord.Embed(title=title, description=message, color=EMBED_COLOR)
    await interaction.response.send_message(
        content=mention, embed=embed, ephemeral=ephemeral
    )


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
