"""This module sets up events in discord based on the calendar events
"""

import hashlib
import logging
from datetime import timedelta, datetime

from discord import ScheduledEvent, Guild, EntityType
from discord.ext import commands

from .common.base_events import BaseEvents


class CalendarEvents(BaseEvents, name="cal_events"):
    """Manages general calendar events for hack&chill and other events in Discord."""

    def __init__(self, bot: commands.Bot):
        self.messages = {}
        super().__init__(bot, calendar_url=bot.config["cal"]["calendar"])

    @staticmethod
    def format_announcement(config: dict, event_data: dict, url: str) -> str:
        """Formats the announcement message with the needed data"""
        return "\n".join(config["cal"]["announcement"]).format(
            title=event_data["name"],
            date=event_data["start_time"].strftime("%H:%M %d/%m/%Y"),
            url=url,
            description=event_data["description"],
        )

    def get_hash(self, event: ScheduledEvent) -> str:
        """Calculates a hash for the event description"""
        return hashlib.md5(event.description.encode()).hexdigest()

    async def handle_events(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """Handles calendar events by creating and updating Discord events"""
        if event_data["start_time"] - timedelta(hours=3) < datetime.now(
            event_data["start_time"].tzinfo
        ):
            # do not edit events 3 hours before the event takes place
            return

        channel_name = (
            "announcements-preview"
            if (
                event_data["start_time"] - timedelta(days=self.delta_days - 1)
                > datetime.now(event_data["start_time"].tzinfo)
            )
            else "announcements"
        )
        channel = guild.get_channel(self.bot.channels[channel_name])

        if scheduled_event:
            message = self.messages.get(self.get_hash(scheduled_event))

            if channel_name == "announcements" and scheduled_event.channel:
                if message:
                    channel = guild.get_channel(
                        self.bot.channels["announcements-preview"]
                    )
                    message = await channel.fetch_message(message)
                    if message.reactions[0].count > 1:
                        # event blocked to announce
                        return

                    await message.delete()
                    self.messages.pop(self.get_hash(scheduled_event))

                logging.info(
                    "Removing preview event %s to announce in announcements",
                    event_data["name"],
                )
                await scheduled_event.delete()
            else:
                # update existing event entry and message
                await scheduled_event.edit(**event_data)
                if message:
                    message = await channel.fetch_message(message)
                    await message.edit(
                        content=self.format_announcement(
                            self.bot.config, event_data, scheduled_event.url
                        )
                    )
        else:
            # create event entry and message
            event = None
            if channel_name == "announcements":
                logging.info("Creating event %s", event_data["name"])
                event = await guild.create_scheduled_event(**event_data)
            else:
                logging.info("Creating preview event %s", event_data["name"])

                # entity_type of voice disallows location entry
                del event_data["location"]
                event_data["entity_type"] = EntityType.voice
                event_data["channel"] = guild.get_channel(
                    self.bot.channels["announcements-voice"]
                )

                event = await guild.create_scheduled_event(**event_data)
            message = await channel.send(
                self.format_announcement(self.bot.config, event_data, event.url)
            )
            await message.add_reaction("🛑")
            self.messages[self.get_hash(event)] = message.id

            logging.info("Created event %s", event_data["name"])


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CalendarEvents(bot))
