"""This module sets up events in discord based on the calendar events
"""

import logging
import sqlite3
from datetime import timedelta, datetime

from discord import ScheduledEvent, Guild, EntityType
from discord.ext import commands

from .common.base_events import BaseEvents


class CalendarEvents(BaseEvents, name="cal_events"):
    """Manages general calendar events for hack&chill and other events in Discord."""

    def __init__(self, bot: commands.Bot):
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

    async def _handle_existing_event(
        self,
        guild: Guild,
        event_data: dict,
        scheduled_event: ScheduledEvent,
        channel,
    ):
        """Handles existing events by updating or deleting them"""
        with sqlite3.connect("events.db") as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM events WHERE event_id = ?",
                (scheduled_event.id,),
            ).fetchone()

        if row and channel.name == "announcements" and row["is_preview"]:
            # The event was a preview event and should be deleted
            channel = guild.get_channel(
                self.bot.channels[self.bot.config["private"]["channels"][0]]
            )

            message = await channel.fetch_message(row["message_id"])
            if message.reactions[0].count > 1:
                logging.info(
                    "Event %s has been blocked, not making public",
                    event_data["name"],
                )
                return
            await message.delete()

            await scheduled_event.delete()
            with sqlite3.connect("events.db") as conn:
                conn.execute(
                    "DELETE FROM events WHERE event_id = ?", (scheduled_event.id,)
                )

            logging.info(
                "Removed preview event %s to announce in announcements",
                event_data["name"],
            )
            return

        # Edit the existing event, message too if it is present in the DB
        if row:
            message = await channel.fetch_message(row["message_id"])
            await message.edit(
                content=self.format_announcement(
                    self.bot.config, event_data, scheduled_event.url
                )
            )
        await scheduled_event.edit(**event_data)

    async def _create_event(self, guild: Guild, event_data: dict, channel):
        """Creates an event in the guild, either as a private preview or as a public announcement"""
        reaction = "❌"

        if channel.name in self.bot.config["private"]["channels"]:
            # The event is created in a voice channel as that is (currently) the only way
            # to create an event with limited visibility. voice disallows location entry.
            del event_data["location"]
            event_data["entity_type"] = EntityType.voice
            event_data["channel"] = guild.get_channel(
                self.bot.channels["announcements-voice"]
            )

            reaction = "🛑"

        logging.info("Creating event %s in %s", event_data["name"], channel.name)

        event = await guild.create_scheduled_event(**event_data)
        message = await channel.send(
            self.format_announcement(self.bot.config, event_data, event.url)
        )

        await message.add_reaction(reaction)

        with sqlite3.connect("events.db") as conn:
            conn.execute(
                "INSERT INTO events (event_id, message_id, is_preview) VALUES (?, ?, ?)",
                (
                    event.id,
                    message.id,
                    1 if channel.name in self.bot.config["private"]["channels"] else 0,
                ),
            )

        logging.info("Created event %s in %s", event_data["name"], channel.name)

    async def handle_events(
        self,
        guild: Guild,
        event_data: dict,
        scheduled_event: ScheduledEvent,
    ):
        """Handles calendar events by creating and updating Discord events"""
        if event_data["start_time"] - timedelta(hours=3) < datetime.now(
            event_data["start_time"].tzinfo
        ):
            # Do not edit events 3 hours before the event takes place
            return

        channel_name = (
            self.bot.config["private"]["channels"][0]
            if (
                event_data["start_time"] - timedelta(days=self.delta_days - 1)
                > datetime.now(event_data["start_time"].tzinfo)
            )
            else self.bot.config["public"]["channels"][0]
        )
        channel = guild.get_channel(self.bot.channels[channel_name])

        if scheduled_event:
            await self._handle_existing_event(
                guild, event_data, scheduled_event, channel
            )
        else:
            await self._create_event(guild, event_data, channel)


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CalendarEvents(bot))
