""""This module sets up events in discord based on the calendar events
"""

import logging
from datetime import timedelta, datetime

from .common.base_events import BaseEvents
from discord import ScheduledEvent, Guild
from discord.ext import commands


class CalendarEvents(BaseEvents, name="cal_events"):
    """Manages general calendar events for hack&chill and other events in Discord."""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot, calendar_url=bot.config["events_calendar"])

    async def handle_events(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """Handles calendar events by creating and updating Discord events."""
        if event_data["start_time"] - timedelta(hours=3) < datetime.now(
            event_data["start_time"].tzinfo
        ):
            # do not edit events 3 hours before the event takes place
            return

        if scheduled_event:
            await scheduled_event.edit(**event_data)
        else:
            event_link = await guild.create_scheduled_event(**event_data)

            message = await self.bot.get_channel(
                self.bot.config["channel"]["announcements"]
            ).send(
                "\n".join(self.bot.config["calendar_announcement"]["message"]).format(
                    title=event_data["name"],
                    date=event_data["start_time"].strftime("%H:%M %d/%m/%Y"),
                    url=event_link.url,
                    description=event_data["description"],
                )
            )
            logging.info("Created general event %s", event_data["name"])

            await message.add_reaction("❌")


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CalendarEvents(bot))
