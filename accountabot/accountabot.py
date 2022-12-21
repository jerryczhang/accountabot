import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from .data import get_users
from .loop import commitment_check_loop


bot = discord.Client(intents=discord.Intents.all())
command_tree = app_commands.CommandTree(bot)
logger = logging.getLogger("discord")


@bot.event
async def on_ready():
    for guild in bot.guilds:
        command_tree.copy_global_to(guild=guild)
        await command_tree.sync(guild=guild)

    get_users().load()
    logger.info("Users loaded")
    commitment_check_loop.start(bot.guilds)


def main() -> int:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if token is None:
        raise RuntimeError("Token environment variable not found")

    bot.run(token)
    return 0
