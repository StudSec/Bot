#!/usr/bin/env python3

# Custom imports
from config import config
from Modules import *

# External imports
from termcolor import colored
import discord

# System imports
import traceback

# Variables
client = discord.Client(intents=discord.Intents.default())
started_up = False
commands = {}
modules = []


@client.event
async def on_ready():
    global started_up
    if not started_up:  # We don't want to reinitialize the modules every time we lose the connection.
        print(f'Logged in as: {colored(client.user.name, "blue")}')
        print(f'id: {colored(client.user.id, "blue")}')
        print(f'version: {colored(discord.__version__, "blue")}')
        print('-'*20)

        print('Servers connected to:')
        for server in client.guilds:
            print("-", colored(server.name, "blue"))
        print('-'*20)

        print("Loaded modules:")
        for module in registry.mods:
            print("-", colored(module.__name__, "yellow"), end="\r")
            if module.__name__ in config.keys():
                module = module(client, config.module.__name__)
            else:
                module = module(client)
            if module.commands.keys() is not None:
                for command in module.commands.keys():
                    commands[command] = module
            modules.append(module)
            print("-", colored(module.name[0], "blue"))

        # Share module list with privileged modules.
        for module in modules:
            if module.type == "Runtime-Privileged":
                module.module_list = modules
        started_up = True
        print('-'*20)
        print(colored("Setup complete", "green"))
    else:
        print('-'*20)
        print(colored("Restarted", "blue"))
        print('-'*20)


@client.event
async def on_message(message):
    if message.author == client.user:       # We don't want the bot responding to itself.
        return

    if message.content.startswith(config["bot"]["prefix"]):
        try:
            async with message.channel.typing():
                response = await commands[message.content[1:].split(" ")[0]].process_message(message)
                if response:
                    # Note: it is possible to break this by having a word over 100 characters,
                    # might need to deal with that.
                    if len(response) > 2000:    # Discord message limit is at 2k chars.
                        response = response.split(' ')
                        ret = ""
                        for r in response:
                            if len(ret) < 1900:
                                ret += r + " "
                            else:
                                if ret.startswith("```"):
                                    ret += "```"
                                    await message.channel.send(ret)
                                    ret = ret.split("\n")[0] + "\n"
                                    ret += r + " "
                                else:
                                    await message.channel.send(ret)
                                    ret = r + " "
                        await message.channel.send(ret)
                    else:
                        await message.channel.send(response)
        except KeyError:
            pass
        except:
            response = "```python\n" + traceback.format_exc()[:-1] + "```"
            if len(response) > 2000:    # Discord message limit is at 2k chars.
                response = response.split(' ')
                ret = ""
                for r in response:
                    if len(ret) < 1900:
                        ret += r + " "
                    else:
                        ret += "\n```"
                        await message.channel.send(ret)
                        ret += "```python\n"
                        ret = ret.split("\n")[0] + "\n"
                        ret += r + " "
                await message.channel.send(ret)
            else:
                await message.channel.send(response)


client.run(config["bot"]["token"])
