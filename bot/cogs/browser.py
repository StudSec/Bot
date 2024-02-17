"""This module is used to interface with a browser for the client-side challs

Some of the web challs are based on client-side attacks such as xss, csrf, etc.
this cog provides the bot with the ability to visit sent websites with the
payloads provided as links.
"""

from discord.ext import commands
from discord.ext.commands import Context
from discord.app_commands import describe

# from selenium.webdriver.firefox.options import Options
# from selenium import webdriver


class Browser(commands.Cog, name="browser"):
    """The class that simulates the browser and visits the link of a specified challenge"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="visit",
        description="Visits a link for a challenge",
    )
    @describe(
        challenge="The challenge to use",
        link="Your crafted link",
    )
    async def visit(self, context: Context, challenge: str, link: str) -> None:
        """The description of my command"""
        await context.send("Hi there!")


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Browser(bot))
