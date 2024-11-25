"""This module defines the shared base class for calendar-based event cogs.
"""

from datetime import datetime, timedelta
import traceback
import logging

import urllib.request
import icalendar
import recurring_ical_events
from markdownify import MarkdownConverter
from discord.ext import commands, tasks
from discord import EntityType, PrivacyLevel, ScheduledEvent, Guild


class ParagraphConverter(MarkdownConverter):  # pylint: disable=missing-class-docstring
    def convert_p(self, el, text, convert_as_inline):
        """Change parsing of p tag to have only one newline instead of 2"""
        return super().convert_p(el, text, convert_as_inline)[:-1]


def md(html, **options):  # pylint: disable=missing-function-docstring
    return ParagraphConverter(**options).convert(html)


class BaseEvents(commands.Cog):
    """A base class for calendar-based event cogs in Discord."""

    def __init__(self, bot: commands.Bot, calendar_url: str, delta_days=10):
        self.bot = bot
        self.calendar_url = calendar_url
        self.delta_days = delta_days
        self.update_events.start()  # pylint: disable=no-member

    @tasks.loop(minutes=1)
    async def update_events(self):
        """Fetches events from the calendar and updates or creates Discord events as needed."""
        with urllib.request.urlopen(self.calendar_url) as u:
            ical_string = u.read()
        calendar = icalendar.Calendar.from_ical(ical_string)
        events = recurring_ical_events.of(calendar).between(
            datetime.now(),
            datetime.now() + timedelta(days=self.delta_days),
        )

        guild = self.bot.get_guild(self.bot.config["server_id"])
        if guild is None:
            return

        scheduled_events = await guild.fetch_scheduled_events()
        for event in events:
            try:
                # NOTE: does not support dates, only events with set start and end times.
                event_data = {
                    "name": event["SUMMARY"],
                    "start_time": event["DTSTART"].dt,
                    "end_time": event["DTEND"].dt,
                    "location": str(event.get("LOCATION", "")),
                    "description": md(str(event.get("DESCRIPTION", ""))),
                    "entity_type": EntityType.external,
                    "privacy_level": PrivacyLevel.guild_only,
                }

                scheduled_event = next(
                    (e for e in scheduled_events if e.name == event_data["name"]), None
                )

                await self.handle_events(guild, event_data, scheduled_event)
            except Exception:  # pylint: disable=broad-exception-caught
                logging.error(
                    "Error in event %s:\n%s",
                    event["SUMMARY"],
                    traceback.format_exc(),
                )

    async def handle_events(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """To be implemented by subclasses to handle specific event types."""
        raise NotImplementedError("Subclasses should implement this method.")

    @update_events.before_loop
    async def before_loop(self):
        """Ensures the bot is ready before the loop starts."""
        await self.bot.wait_until_ready()
