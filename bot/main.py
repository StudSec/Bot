"""This module is the main entrypoint of the bot. 

In this file, the `StudBot` is defined, initialized, and extended with the cogs.
Run this file using `poetry` as described in the `README.md`
"""

import os
import logging
import json

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv
from termcolor import colored


class StudBot(commands.Bot):
    """This is the entrypoint when running the bot, with all the initialization and friends"""

    def __init__(self) -> None:
        """
        Initializes (in order)
        - The different configurations inside the class, such as the path;
        - The intents and sets the prefix for `super`;
        """
        self.path = f"{os.path.realpath(os.path.dirname(__file__))}"
        with open(f"{self.path}/config.json", "r", encoding="utf-8") as file:
            self.config = json.load(file)

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guild_messages = True

        # prefix only used for sync command
        super().__init__(intents=intents, command_prefix="!")

    async def load_cogs(self) -> None:
        """Loads in all the cogs defined in the `bot/cogs` directory"""
        for file in os.listdir(f"{self.path}/cogs"):
            if file.endswith(".py") and not file == "ctf.py":
                logging.info("Loading cog: %s", colored(file, "blue"))
                await self.load_extension(f"bot.cogs.{file[:-3]}")

    async def setup_hook(self) -> None:
        """
        Runs when the bot starts for the first time.
        entrypoint to call all the other setup functions
        """
        logging.info("-" * 20)
        logging.info("Logged in as: %s", colored(self.user.name, "blue"))
        logging.info("User ID is: %s", colored(self.user.id, "blue"))
        logging.info("discord.py version: %s", colored(discord.__version__, "blue"))
        logging.info("Connected to:")
        async for server in self.fetch_guilds():
            logging.info("+ %s", colored(server, "blue"))
        logging.info("-" * 20)

        await self.load_cogs()

    async def on_command_error(  # pylint: disable=arguments-differ, unused-argument
        self, context: Context, error
    ) -> None:
        """
        The function handles error of prefixed commands, which is only used for sync,
        so commands.CommandNotFound must be ignored
        """
        if isinstance(error, commands.CommandNotFound):
            return await context.send("This command doesn't exist!", ephemeral=True)
        if isinstance(error, commands.MissingPermissions):
            return await context.send("Missing permissions!", ephemeral=True)
        raise error

    async def on_tree_error(self, interaction: discord.Interaction, error) -> None:
        """Handle errors from slash commands, such as cooldown

        Args:
            interaction: The interaction context of the messages
            error: The encountered error of the command
        """
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(
                f"You are on cooldown. Try again in **{round(error.retry_after)} seconds**!",
                ephemeral=True,
            )
        raise error


def main() -> None:
    """The main function. Call this to start the bot"""
    logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

    load_dotenv()
    bot = StudBot()
    bot.tree.on_error = bot.on_tree_error
    bot.run(os.getenv("DISCORD_TOKEN"))



if __name__ == "__main__":
    main()
