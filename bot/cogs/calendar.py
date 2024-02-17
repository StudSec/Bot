""""This module sets up events in discord based on the calendar events

To automate the work of making events on discord for the hack&chills, this cog
checks the StudSec calendar and creates a matching event for a hack&chill listed
there.
"""

from discord.ext import commands
from discord.ext.commands import Context


class YourClassName(commands.Cog, name="yourClassName"):
    def __init__(self, bot) -> None:
        self.bot = bot

    # NOTE: this is for a command, non command cogs won't need this
    @commands.hybrid_command(
        name="yourCommandName",
        description="The description of my command",
    )
    async def yourcommandhere(self, context: Context) -> None:
        """The description of my command

        :param context: The application command context.
        """
        return


async def setup(bot) -> None:
    await bot.add_cog(YourClassName(bot))
