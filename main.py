from dotenv import load_dotenv
import os

from accountabot.accountabot import bot

if __name__ == "__main__":
    load_dotenv()

    bot.run(os.getenv("DISCORD_TOKEN"))
