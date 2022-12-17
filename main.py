import os

from dotenv import load_dotenv

from accountabot import bot

if __name__ == "__main__":
    load_dotenv()

    bot.run(os.getenv("DISCORD_TOKEN"))
