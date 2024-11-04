""""This module sets up CTF events in discord based on the calendar events
"""

import logging
from datetime import datetime

import pytz
from common.base_events import BaseEvents
from discord import ScheduledEvent, User, Guild, PermissionOverwrite
from discord.ext import commands


class CTFEvents(BaseEvents, name="ctf_events"):
    """Manages CTF related integration stuff in the discord"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot, calendar_url=bot.config["ctf_calendar"])

    async def handle_events(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent | None
    ):
        """Handles CTF-specific events by creating and updating Discord events and channels."""
        if not scheduled_event:
            # This is a bit of a conflict, in the calendar we just want the days of
            # the event to be marked off, especially because its a multi-day event.
            # But the event itself we might want to manually update the times.
            # Because of this, we don't make the event editable after creation.

            timezone = pytz.timezone("Europe/Amsterdam")
            event_data["start_time"] = timezone.localize(
                datetime.combine(event_data["start_time"], datetime.min.time())
            )
            event_data["end_time"] = timezone.localize(
                datetime.combine(event_data["end_time"], datetime.max.time())
            )
            await guild.create_scheduled_event(**event_data)
            logging.info("Created CTF event %s", event_data["name"])

            for channel_category, _ in guild.by_category():
                if (
                    channel_category
                    and channel_category.name
                    == f"CTFs - {event_data["start_time"].strftime('%Y')}"
                ):
                    category = channel_category
                    break
            else:
                category = await guild.create_category(
                    f"CTFs - {event_data["start_time"].strftime('%Y')}"
                )

            overwrites = {
                guild.default_role: PermissionOverwrite(read_messages=False),
            }

            forum = await category.create_forum(
                event_data["name"], overwrites=overwrites
            )
            await forum.create_thread(
                name="General",
                content=f"General discussion thread for {event_data["name"]}",
            )
            logging.info("Created CTF forum %s", event_data["name"])

            # This method only works for messages, to my knowledge there is currently no way to
            # pin forums threads - Aidan
            # await init_post.pin()

            # Add tags, this can be done in the forum creation but this is more readable.
            await forum.create_tag(name="busy")
            await forum.create_tag(name="done")
            await forum.create_tag(name="stuck")

    async def manage_ctf_channel(self, event: ScheduledEvent, user: User, read):
        """Manages users being added or removed from a channel"""
        for category, channels in event.guild.by_category():
            if (
                not category
                or category.name != f"CTFs - {event.start_time.strftime('%Y')}"
            ):
                continue

            channel = next(
                (c for c in channels if c.name == event.name.replace(" ", "-").lower()),
                None,
            )
            if channel:
                await channel.set_permissions(user, read_messages=read)
                logging.info(
                    "%s %s to CTF %s",
                    ("Added" if read else "Removed"),
                    user.name,
                    event.name,
                )

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(
        self, event, user
    ):  # pylint: disable=missing-function-docstring
        await self.manage_ctf_channel(event, user, True)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(
        self, event, user
    ):  # pylint: disable=missing-function-docstring
        await self.manage_ctf_channel(event, user, False)


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CTFEvents(bot))
