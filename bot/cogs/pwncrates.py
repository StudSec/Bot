"""This module provides integration between pwncrates and discord

To provide some extra functionaly, this cog provides the roles, scoreboard, and
dates of the solves integration on the discord for the pwncrates site.
"""

import json
import logging
import traceback
import itertools

import discord
import requests
from discord.utils import get
from discord.ext import commands, tasks


class Pwncrates(commands.Cog, name="pwncrates"):
    """The class that provides the pwncrates integration"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.update_scoreboard.start()  # pylint: disable=no-member

    @staticmethod
    def get_scoreboard() -> json:
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
            new_scoreboard += f"{user['position']:<2} {user['username'].replace('`', ''):<31} {user['score']:>5}\n"     # pylint: disable=line-too-long
        new_scoreboard += "```"

        scoreboard_channel = self.bot.get_channel(
            self.bot.config["channel"]["scoreboard"]
        )
        if scoreboard_channel is None:
            return

        try:
            latest_message = await get(scoreboard_channel.history())
            if new_scoreboard == latest_message.content:
                return
            if latest_message:
                await latest_message.delete()
            await scoreboard_channel.send(new_scoreboard)
            await self.adjust_roles(scoreboard, scoreboard_channel)
        except ConnectionRefusedError:
            return
        except discord.errors.Forbidden:
            logging.error("Failed to set roles; Missing permission role")
        except Exception:  # pylint: disable=broad-exception-caught
            logging.error("Error in pwncrates, %s", traceback.format_exc())
            return

    @update_scoreboard.before_loop
    async def before_loop(self) -> None:
        """Make sure the bot is ready"""
        await self.bot.wait_until_ready()

    async def adjust_roles(self, scoreboard: json, channel: discord.channel) -> None:
        """Updates the rank roles, if needed"""
        roles = list(
            itertools.chain.from_iterable(
                [
                    [get(channel.guild.roles, id=self.bot.config["roles"]["0x01"])],
                    [get(channel.guild.roles, id=self.bot.config["roles"]["0x05"])] * 4,
                    [get(channel.guild.roles, id=self.bot.config["roles"]["0x0A"])] * 5,
                ]
            )
        )

        for i, user in enumerate(scoreboard[:10]):
            try:
                discord_id = self.get_discord_id(user["user_id"])
                discord_user = await channel.guild.fetch_member(discord_id)
            except (discord.errors.NotFound, TypeError):
                continue

            if not discord_user:
                continue    # User might not be in the discord server

            if roles[i] not in discord_user.roles:
                await discord_user.add_roles(roles[i])


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Pwncrates(bot))
