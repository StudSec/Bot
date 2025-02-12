"""This module provides integration between pwncrates and discord

To provide some extra functionaly, this cog provides the roles, scoreboard, and
dates of the solves integration on the discord for the pwncrates site.
"""

import json
import logging
import traceback
import itertools

import requests
import discord
from discord import Guild, Role
from discord.utils import get
from discord.ext import commands, tasks


class Pwncrates(commands.Cog, name="pwncrates"):
    """The class that provides the pwncrates integration"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.roles: list[Role] = []
        self.update_scoreboard.start()  # pylint: disable=no-member

    @staticmethod
    def get_scoreboard() -> dict:
        """Gets the scoreboard from the studsec api in json form"""
        return json.loads(
            requests.get("https://ctf.studsec.nl/api/scoreboard", timeout=10).text
        )

    @staticmethod
    def get_discord_id(user_id) -> int:
        """Gets the discord id for the specific user_id"""
        return int(
            json.loads(
                requests.get(
                    f"https://ctf.studsec.nl/api/discord_id/{user_id}", timeout=10
                ).text
            )["discord_id"]
        )

    async def adjust_roles(
        self, scoreboard: dict, channel: discord.TextChannel
    ) -> None:
        """Updates the rank roles, if needed"""
        for i, user in enumerate(scoreboard[:10]):
            try:
                discord_id = self.get_discord_id(user["user_id"])
                discord_user = await channel.guild.fetch_member(discord_id)
            except (discord.errors.NotFound, TypeError):
                continue

            if not discord_user:
                continue  # User might not be in the discord server

            if self.roles[i] not in discord_user.roles:
                await discord_user.add_roles(self.roles[i])

    @tasks.loop(seconds=30)
    async def update_scoreboard(self) -> None:
        """A loop to update the scoreboard on discord and (re)assign rank roles, if needed"""

        try:
            scoreboard = self.get_scoreboard()
        except requests.exceptions.RequestException:
            return  # something failed with the request, return and let the next loop try again

        new_scoreboard = "```\n"
        # API already orders users by score, we can take top 25
        for user in scoreboard[:25]:
            new_scoreboard += f"{user['position']:<2} {user['username'].replace('`', ''):<31} {user['score']:>5}\n"  # pylint: disable=line-too-long
        new_scoreboard += "```"

        guild: Guild = self.bot.get_guild(self.bot.config["server_id"])
        scoreboard_channel = guild.get_channel(self.bot.channels["scoreboard"])
        if not isinstance(scoreboard_channel, discord.TextChannel):
            return

        try:
            latest_message = await get(scoreboard_channel.history())
            if latest_message and new_scoreboard != latest_message.content:
                await latest_message.edit(content=new_scoreboard)
            elif not latest_message:
                await scoreboard_channel.send(new_scoreboard)
            await self.adjust_roles(scoreboard, scoreboard_channel)
        except ConnectionRefusedError:
            return
        except discord.errors.Forbidden:
            logging.error("Failed to set roles; Missing permission role")
        except Exception:  # pylint: disable=broad-exception-caught
            logging.error("Error in pwncrates, %s", traceback.format_exc())
            return

    async def setup_roles(self, guild: Guild) -> None:
        """Gets the roles and fills the roles class member with them"""
        for name, i in itertools.zip_longest(
            self.bot.config["pwncrates"]["roles"], [1, 4, 5]
        ):
            role = next((r for r in guild.roles if r.name == name), None)
            if not role:
                role = await guild.create_role(name=name)
            self.roles += [role] * i

    @update_scoreboard.before_loop
    async def before_loop(self) -> None:
        """Make sure the bot is ready, clean scoreboard channel, and get/make needed roles"""
        guild: Guild = self.bot.get_guild(self.bot.config["server_id"])

        await self.bot.wait_until_ready()
        await self.setup_roles(guild)


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Pwncrates(bot))
