"""This module is used to interface with a browser for the client-side challs

Some of the web challs are based on client-side attacks such as xss, csrf, etc.
this cog provides the bot with the ability to visit sent websites with the
payloads provided as links.
"""

import base64
import logging
import time
import re
from collections.abc import Callable

import discord
from discord import app_commands
from discord.ext import commands
from selenium.webdriver.firefox.options import Options
from selenium import webdriver

try:
    from .ctf import corn, exss, mlb  # type: ignore
except ImportError:
    logging.warning("CTF module not found, using default values")
    corn = {"password": "flag"}
    exss = mlb = {"flag": "flag"}


class Browser(commands.Cog, name="browser"):
    """The class that simulates the browser and visits the link of a specified challenge"""

    def __init__(self, bot) -> None:
        self.browser = None

        self.bot = bot
        self.challenges: dict[str, Callable[[webdriver.Firefox], None]] = {
            "corn": self.corn,
            "exss": self.exss,
            "mlb": self.my_little_browser,
        }

    @app_commands.checks.cooldown(1.0, 60.0, key=lambda i: (i.user.id))
    @app_commands.command(name="visit", description="Visits a link for a challenge")
    @app_commands.describe(
        challenge="The challenge to setup for",
        url="Your crafted url",
    )
    @app_commands.choices(
        challenge=[
            app_commands.Choice(name="EX-SS", value="exss"),
            app_commands.Choice(name="My Little Browser", value="mlb"),
            app_commands.Choice(name="corn", value="corn"),
        ]
    )
    async def visit(
        self,
        interaction: discord.Interaction,
        challenge: app_commands.Choice[str],
        url: str,
    ) -> None:
        """The command to visit a given link for a challenge

        Args:
            interaction: The interaction context provided
            challenge: The challenge to setup for
            url: The url to visit

        Raises:
            CommandOnCooldown: If a user tries to use it within a 60 second cooldown
        """

        challenge_choice = challenge.value

        _URL_REGEX = re.compile(  # pylint: disable=invalid-name
            r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b"
            r"([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
        )

        if not isinstance(interaction.channel, discord.channel.DMChannel):
            return await interaction.response.send_message(
                "This command can only be used in DMs!", ephemeral=True
            )

        if challenge_choice not in self.challenges:
            return await interaction.response.send_message(
                "Invalid challenge chosen!", ephemeral=True
            )

        if not re.match(_URL_REGEX, url):
            return await interaction.response.send_message(
                "Invalid URL, try again", ephemeral=True
            )

        await interaction.response.send_message("Visiting link...")
        message = await interaction.original_response()
        browser = self.setup_challenge(challenge_choice)

        try:
            browser.get(url)
        except Exception:  # pylint: disable=broad-exception-caught
            await message.edit(content="Unable to visit link!")
            return

        time.sleep(10)  # Give the JS a second to execute
        await message.edit(content="Visited link!")
        browser.quit()

    def setup_challenge(self, challenge: str) -> webdriver.Firefox:
        """
        This function does browser setup thats common, and then calls the
        specific challenge setup function

        Args:
            challenge: a string of the challenge name
        """
        opts = Options()
        opts.set_headless()

        profile = webdriver.FirefoxProfile()
        profile.DEFAULT_PREFERENCES["frozen"][  # type: ignore # pylint: disable=unsubscriptable-object
            "network.cookie.cookieBehavior"
        ] = 4
        browser = webdriver.Firefox(options=opts, firefox_profile=profile)
        browser.set_page_load_timeout(10)
        browser.delete_all_cookies()

        self.challenges[challenge](browser)

        browser.get("about:newtab")
        return browser

    @staticmethod
    def corn(browser: webdriver.Firefox) -> None:
        """This function sets up for the **corn** challenge"""
        browser.get("http://challs.studsec.nl:5100/login")
        username = browser.find_element_by_id("username")
        password = browser.find_element_by_id("password")
        username.send_keys("admin")
        password.send_keys(corn["password"])
        browser.find_element_by_name("login").click()

    @staticmethod
    def exss(browser: webdriver.Firefox) -> None:
        """This function sets up for the **exss** challenge"""
        browser.get(
            "http://challs.studsec.nl:5080/?"
            + base64.b64encode(exss["flag"].encode()).decode("ascii")
        )

    @staticmethod
    def my_little_browser(browser: webdriver.Firefox) -> None:
        """This function sets up for the **my little browser** challenge"""
        browser.get(
            "http://challs.studsec.nl:5480/?page="
            + base64.b64encode(mlb["flag"].encode()).decode("ascii")
        )


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Browser(bot))
