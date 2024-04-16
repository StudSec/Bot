"""This module provides the ability to a moderator to sync the commands

To register changes to commands, the bot must be resynced 
"""

from discord.ext import commands
from discord.ext.commands import Context


class Admin(commands.Cog, name="admin"):
    """The sync class. Provides the functionality to sync"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: Context) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        """
        await ctx.bot.tree.sync()

    @commands.command(
        name="list",
        description="List loaded cogs.",
    )
    @commands.has_permissions(administrator=True)
    async def list_cogs(self, ctx: Context) -> None:
        """
        Lists loaded cogs

        :param context: The command context.
        """
        msg = "Loaded cogs:\n```\n"
        for cog in ctx.bot.cogs:
            msg += f"- {cog}\n"
        msg += "```"

        await ctx.send(msg)


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Admin(bot))
