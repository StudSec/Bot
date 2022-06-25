"""
This handles the integration between CTFD and discord, displaying the scoreboard and giving roles.
"""
# Custom imports
from . import registry

# External imports
from discord.ext import tasks
from discord.utils import get
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

    @tasks.loop()
    async def update_scoreboard(self):
        await asyncio.sleep(6)
        scoreboard = self.get_scoreboard()

        msg = "```\n"
        for user in scoreboard:
            if user['pos'] > 25:
                break
            msg += f"{user['pos']} {user['name']}" + " "*(40 - len(user['name']) - len(str(user['pos'])) -
                                                          len(str(user['score']))) + f"{user['score']}\n"
        msg += "```"

        latest_messages = (await self.client.get_channel(988434368655687760).history(limit=5).flatten())

        for i in latest_messages:
            if msg == i.content:
                return

        await self.adjust_roles(scoreboard)

        for i in latest_messages:
            await i.delete()

        channel = self.client.get_channel(988434368655687760)
        await channel.send(msg)

    @staticmethod
    def get_scoreboard():
        return json.loads(requests.get("https://ctf.studsec.nl/api/v1/scoreboard").text)["data"]

    @staticmethod
    def get_discord_id(id):
        return int(json.loads(requests.get(f"https://ctf.studsec.nl/api/v1/discord/ctf2disc/{id}").text)["data"]["id"])

    async def adjust_roles(self, scoreboard):
        roles = {
            "0x0A": get(self.client.get_channel(988434368655687760).guild.roles, id=988439047296917526),
            "0x05": get(self.client.get_channel(988434368655687760).guild.roles, id=988439003646787664),
            "0x01": get(self.client.get_channel(988434368655687760).guild.roles, id=988438939394248784)
        }
        for user in scoreboard:
            try:
                acc = await self.client.get_channel(988434368655687760).guild.fetch_member(
                    self.get_discord_id(user["account_id"]))
            except:
                continue
            if not acc:
                continue
            await acc.remove_roles(*list(roles.values()))
            if user["pos"] == 1:
                await acc.add_roles(roles["0x01"])
            elif 1 < user["pos"] < 6:
                await acc.add_roles(roles["0x05"])
            elif 5 < user["pos"] < 11:
                await acc.add_roles(roles["0x0A"])


registry.register(CTFD)


