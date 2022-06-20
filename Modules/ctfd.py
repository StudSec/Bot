"""
This handles the integration between CTFD and discord, displaying the scoreboard and giving roles.
"""
# Custom imports
from . import registry

# External imports
from discord.ext import tasks
import requests
import asyncio

# Builtins
import json


class CTFD:
    def __init__(self, client):
        self.commands = {
        }
        self.name = ["CTFD"]
        self.category = ["CTF"]
        self.client = client
        self.type = "Startup"
        self.update_scoreboard.start()

    async def process_message(self, message):
        pass

    @tasks.loop
    async def update_scoreboard(self):
        await asyncio.sleep(60)
        scoreboard = self.get_scoreboard()
        self.adjust_roles(scoreboard)
        msg = "```\n"
        for user in scoreboard:
            if user['pos'] > 25:
                break
            msg += f"{user['pos']} {user['name']}" + " "*(20 - len(user['name'])) + f"{user['score']}\n"
        msg += "```"

        latest_messages = (await self.get_channel(988434368655687760).history(limit=5).flatten())

        for i in latest_messages:
            if msg == i:
                return

        channel = self.client.get_channel(988434368655687760)
        await channel.send(msg)

    @staticmethod
    def get_scoreboard():
        return json.loads(requests.get("https://ctf.studsec.nl/api/v1/scoreboard").text)["data"]

    # TODO: gives 0x01, 0x05, 0x0A roles to top 10.
    def adjust_roles(self, scoreboard):
        pass


registry.register(CTFD)
