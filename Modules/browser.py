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
import base64
import time
import re
import os

try:
    from . import ctf

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
            self.challenges = {
                "corn": self.corn,
                "exss": self.exss,
                "mlb": self.my_little_browser
            }
            self.users = {}
            self.setup_browser()

        async def process_message(self, message):
            if not isinstance(message.channel, discord.channel.DMChannel):  # Module only works in DMs
                return
            if message.content.split(" ")[0][1:] in self.commands.keys():
                return await self.commands[message.content.split(" ")[0][1:]](message)

        # This function tests the basic message sending functionality.
        async def visit(self, msg):
            if len(msg.content.split(" ")) < 2:
                return "Usage: !visit <url>"
            url = msg.content.split(" ")[1]
            if not re.match(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@"
                            r":%_\+.~#?&//=]*)", url):
                return "Invalid URL"

            if msg.author in self.users.keys() and time.time() - self.users[msg.author] < 60:
                return "I can only visit one link every minute."
            self.users[msg.author] = time.time()

            status_msg = await msg.channel.send("Setting up")

            self.setup_browser()
            await status_msg.edit(content="Visiting link..")

            try:
                self.browser.get(url)
            except Exception:
                await status_msg.edit(content="Unable to connect.")
                return

            time.sleep(10)   # Give the JS a second to execute

            await status_msg.edit(content="Link visited.")

            os.system("killall firefox")
            return

        def setup_browser(self):
            opts = Options()
            opts.set_headless()
            assert opts.headless
            self.browser = webdriver.Firefox(options=opts)
            self.browser.set_page_load_timeout(10)
            self.browser.delete_all_cookies()    # Probably redundant.

            # Initialize the individual challenges
            for i in self.challenges.keys():
                try:
                    self.challenges[i]()
                except Exception as e:
                    print(e)

            # Prevent leakage from the setup.
            self.browser.get("about:newtab")

        def corn(self):
            self.browser.get("http://challs.studsec.nl:5100/login")
            username = self.browser.find_element_by_id("username")
            password = self.browser.find_element_by_id("password")
            username.send_keys("admin")
            password.send_keys(ctf.corn["password"])
            self.browser.find_element_by_name("login").click()

        def exss(self):
            self.browser.get("http://challs.studsec.nl:5080/?" + base64.b64encode(ctf.exss["flag"].encode()).decode('ascii'))

        def my_little_browser(self):
            self.browser.get("http://challs.studsec.nl:5480/?page=" + base64.b64encode(ctf.mlb["flag"].encode()).decode('ascii'))


    registry.register(Browser)
except ImportError:
    pass
