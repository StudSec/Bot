"""This module is the main entrypoint of the bot. 

In this file, the `StudSecBot` is defined, initialized, and extended with the cogs.
Run this file using `poetry` as described in the `README.md`
"""

import os
import logging

import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from termcolor import colored


class StudSecBot(commands.Bot):
    """This is the entrypoint when running the bot, with all the initialization and friends"""

    def __init__(self) -> None:
        """
        Initializes (in order)
        - The different configurations inside the class, such as the path and prefix;
        - The intents and sets the prefix for `super`;
        """
        self.prefix = "!"
        self.path = f"{os.path.realpath(os.path.dirname(__file__))}"

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(intents=intents, command_prefix=self.prefix)

    async def load_cogs(self) -> None:
        """Loads in all the cogs defined in the `bot/cogs` directory"""
        for file in os.listdir(f"{self.path}/cogs"):
            if file.endswith(".py"):
                logging.info("Loading cog: %s", colored(file, "light_blue"))
                await self.load_extension(f"bot.cogs.{file[:-3]}")

    async def setup_hook(self) -> None:
        """Runs when the bot starts for the first time. entrypoint to call all the other setup functions"""
        logging.info("-" * 20)
        logging.info("Logged in as: %s", colored(self.user.name, "blue"))
        logging.info("User ID is: %s", colored(self.user.id, "blue"))
        logging.info("discord.py version: %s", colored(discord.__version__, "blue"))
        logging.info("-" * 20)

        await self.load_cogs()


def main() -> None:
    """The main function. Call this to start the bot"""
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

    load_dotenv()
    bot = StudSecBot()
    bot.run(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    main()
