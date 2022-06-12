"""
This module is used to interface with a browser. Allowing for client-side web attacks such as xss, csrf, etc.
"""
# Custom imports
from . import registry

# External imports
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
import discord


# Builtins
import time
import re


class Browser:
    def __init__(self, client):
        self.commands = {
            "visit": self.visit,
        }
        self.name = ["Browser"]
        self.category = ["CTF"]
        self.client = client
        self.type = "Runtime"
        self.browser = None
        self.challenges = {}
        self.users = {}

    async def process_message(self, message):
        if not isinstance(message.channel, discord.channel.DMChannel):  # Module only works in DMs
            return
        if message.content.split(" ")[0][1:] in self.commands.keys():
            return self.commands[message.content.split(" ")[0][1:]](message)

    # This function tests the basic message sending functionality.
    def visit(self, msg):
        if len(msg.content.split(" ")) < 2:
            return "Usage: !visit <url>"
        url = msg.content.split(" ")[1]
        if not re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@"
                        r":%_\+.~#?&//=]*)", url):
            return "Invalid URL"

        if msg.author in self.users.keys() and time.time - self.users[msg.author] < 5:
            return "I can only visit one link every 5 seconds."
        self.users[msg.author] = time.time()

        self.setup_browser()
        self.browser.get(url)

        return "Visiting link..."

    def setup_browser(self):
        opts = Options()
        opts.set_headless()
        assert opts.headless
        self.browser = webdriver.Firefox(options=opts)
        self.browser.set_page_load_timeout(10)

        # Initialize the individual challenges
        for i in self.challenges.keys:
            i()


registry.register(Browser)
