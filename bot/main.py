"""This module is the main entrypoint of the bot.

In this file, the `StudBot` is defined, initialized, and extended with the cogs.
Run this file using `poetry` as described in the `README.md`
"""

import os
import logging
import json
import sqlite3
import sys

import discord
from discord import app_commands, PermissionOverwrite, Interaction
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
        self.channels: dict[str, int] = {}
        self.path = f"{os.path.realpath(os.path.dirname(__file__))}"
        self.shared = os.path.abspath(f"{self.path}/..") + "/shared"

        with open(f"{self.path}/config.json", "r", encoding="utf-8") as file:
            self.config = json.load(file)
        if server_id := os.getenv("SERVER_ID"):
            self.config["server_id"] = int(server_id)
        else:
            logging.error("SERVER_ID not set")
            sys.exit(1)

        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.guild_messages = True
        intents.guild_scheduled_events = True

        # prefix only used for sync command
        super().__init__(intents=intents, command_prefix="!")

    async def setup_channels(self) -> None:
        """Gets or sets up the channels, possible restricted, and sets the channels class member"""
        guild = self.get_guild(self.config["server_id"])
        if not guild:
            logging.error("Guild not found")
            return

        public = self.config["public"]
        private = self.config["private"]

        for name in public["channels"] + private["channels"]:
            channel = next((c for c in guild.channels if c.name == name), None)
            if not channel:
                logging.info("Creating channel %s", name)
                args = {"name": name}

                if name in private["channels"]:
                    args["overwrites"] = {
                        guild.default_role: PermissionOverwrite(view_channel=False),
                        **{
                            role: PermissionOverwrite(view_channel=True)
                            for role in guild.roles
                            if role.name in private["roles"]
                        },
                    }

                channel = (
                    await guild.create_voice_channel(**args)
                    if "voice" in name
                    else await guild.create_text_channel(**args)
                )

            self.channels[name] = channel.id
            logging.info("Gathered channel %s", name)

    async def create_db(self) -> None:
        """Creates the database for the events cog"""
        with sqlite3.connect(f"{self.shared}/events.db") as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS events "
                + "(event_id INTEGER PRIMARY KEY, message_id INTEGER, is_preview INTEGER)"
            )

    async def load_cogs(self) -> None:
        """Loads in all the cogs defined in the `bot/cogs` directory"""
        for file in os.listdir(f"{self.path}/cogs"):
            if file.endswith(".py") and not file == "ctf.py":
                logging.info("Loading cog: %s", colored(file, "blue"))
                await self.load_extension(f"bot.cogs.{file[:-3]}")

    async def on_ready(self):
        """
        Runs when the bot is ready and fully connected
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

        await self.create_db()
        await self.setup_channels()
        await self.load_cogs()

    async def on_command_error(  # pylint: disable=arguments-differ, unused-argument
        self, context: Context, error
    ) -> None:
        """
        The function handles error of prefixed commands, which is only used for sync,
        so commands.CommandNotFound must be ignored
        """
        if isinstance(error, commands.CommandNotFound):
            await context.send("This command doesn't exist!", ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await context.send("Missing permissions!", ephemeral=True)
        else:
            raise error

    async def on_tree_error(self, interaction: Interaction, error) -> None:
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
    bot.tree.on_error = bot.on_tree_error  # type: ignore
    if token := os.getenv("DISCORD_TOKEN"):
        bot.run(token, log_level=logging.INFO)
    else:
        logging.error("DISCORD_TOKEN not set")


if __name__ == "__main__":
    main()
