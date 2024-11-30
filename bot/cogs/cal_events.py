"""This module sets up events in discord based on the calendar events
"""

import logging
from datetime import timedelta, datetime

from discord import ScheduledEvent, Guild, EntityType, Message
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
            message: Message = self.messages.get(
                event_data["start_time"].strftime("%H:%M %d/%m/%Y")
            )

            if channel_name == "announcements" and (
                (
                    message
                    and message.channel.name == "announcements-preview"
                    and message.reactions[0].count <= 1
                )
                or scheduled_event.channel
            ):
                logging.info(
                    "Removing preview event %s to announce in announcements",
                    event_data["name"],
                )
                if message:
                    del self.messages[
                        event_data["start_time"].strftime("%H:%M %d/%m/%Y")
                    ]
                    await message.delete()
                await scheduled_event.delete()
                return

            # update existing event entry and message
            await scheduled_event.edit(**event_data)
            if message:
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
            self.messages[event_data["start_time"].strftime("%H:%M %d/%m/%Y")] = message

            logging.info("Created event %s", event_data["name"])
            await message.add_reaction("❌")

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: ScheduledEvent):
        """
        Triggered whenever a scheduled event is removed
        Used to remove message entry on event complete
        """
        del self.messages[event.start_time.strftime("%H:%M %d/%m/%Y")]


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CalendarEvents(bot))
