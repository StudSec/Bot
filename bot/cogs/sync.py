"""This module provides the ability to a moderator to sync the commands

To register changes to commands, the bot must be resynced 
"""

from discord.ext import commands
from discord.ext.commands import Context


class Sync(commands.Cog, name="sync"):
    """The sync class. Provides the functionality to sync"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @commands.has_permissions(manage_messages=True)
    async def sync(self, ctx: Context) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        """
        await ctx.bot.tree.sync()
        await ctx.send("Sync complete!")


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Sync(bot))
