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
                "exss": self.exss
            }
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

            if msg.author in self.users.keys() and time.time() - self.users[msg.author] < 60:
                return "I can only visit one link every minute."
            self.users[msg.author] = time.time()

            try:
                self.setup_browser()
                self.browser.get(url)
            except Exception:
                return "Unable to connect."

            time.sleep(10)   # Give the JS a second to execute

            return "Link visited"

        def setup_browser(self):
            opts = Options()
            opts.set_headless()
            assert opts.headless
            self.browser = webdriver.Firefox(options=opts)
            self.browser.set_page_load_timeout(10)
            self.brower.delete_all_cookies()    # Probably redundant.

            # Initialize the individual challenges
            for i in self.challenges.keys():
                self.challenges[i]()

        def corn(self):
            self.browser.get("http://146.190.16.124:5100/login")
            username = self.browser.find_element_by_id("username")
            password = self.browser.find_element_by_id("password")
            username.send_keys("admin")
            password.send_keys(ctf.corn["password"])
            self.browser.find_element_by_name("login").click()

        def exss(self):
            self.browser.get("http://146.190.16.124:5080/")
            cookie = self.browser.find_element_by_id("add-cookie")
            cookie.send_keys(ctf.exss["flag"])
            self.browser.find_element_by_id("add-cookie").click()


    registry.register(Browser)
except ImportError:
    pass