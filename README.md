# Bot
The *official* StudSec bot written in Python using [discord.py](https://discordpy.readthedocs.io/en/stable/).

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installation and Usage
To install the needed dependencies, first make sure you have [Poetry](https://python-poetry.org/docs/#installation)
 installed. After which, you can install the dependencies using

```sh
poetry install
```

Then, to run the bot needs a discord token, which needs to be put in a new 
 `.env` file like so

```
DISCORD_TOKEN=your_token_here
```

After the discord token is set, you can run the bot using

```sh
poetry run bot
```

## Development
If you would like to extend StudBots functionality, feel free to create a pull
 request. In the message please include a brief description of the functionality
 you added / changed, please note we will review any pull request and
 change/reject if needed. If you'd like help developing, debugging, ranting or
 just want to lurk, you can join our development discord server. The invite code
 is `gNFQcvbevF`.

The recommended development environment to develop in is using a python venv.
 You can enter one provided by poetry using

```sh
poetry shell
```

on top of this, this project (tries to) adhere to the google python style, and
 uses pylint for its linting and black for its styling. To do this simply enter
 a poetry shell and run
 ```sh
 pylint bot
 ```

## Documentation
To add a cog, use the following template

```py
"""
Module description
"""

from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Context


class YourClassName(commands.Cog, name="yourClassName"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # NOTE: this is for a command, non command cogs won't need this
    @app_commands.command(
        name="yourCommandName",
        description="The description of my command",
    )
    async def yourcommandhere(self, context: Context) -> None:
        """The description of my command

        :param context: The application command context.
        """
        return


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(YourClassName(bot))
```

## TODO
Some features that could be added
- load/reload/unload functionality?
- status message(s)?
- update selenium?
- update ctf flag loading?
- remove id hardcoding
