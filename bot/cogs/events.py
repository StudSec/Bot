"""This module defines the shared base class for calendar-based event cogs."""

import traceback
import logging
from datetime import datetime, timedelta

import urllib.request
import icalendar
import recurring_ical_events  # type: ignore
from markdownify import MarkdownConverter  # type: ignore
from discord import EntityType, PrivacyLevel, ScheduledEvent, User
from discord.ext import commands, tasks
from .common.handler import Handler  # type: ignore


class ParagraphConverter(MarkdownConverter):  # pylint: disable=missing-class-docstring
    def convert_p(self, el, text, convert_as_inline):
        """Change parsing of p tag to have only one newline instead of 2"""
        return super().convert_p(el, text, convert_as_inline)[:-1]


def md(html, **options):  # pylint: disable=missing-function-docstring
    return ParagraphConverter(**options).convert(html)


class Events(commands.Cog, name="events"):
    """A class that deals with fetching events, and calling the appropriate handler."""

    def __init__(self, bot):
        self.bot = bot
        self.handlers = Handler.get_handlers(self.bot)
        self.update_events.start()  # pylint: disable=no-member
        self.guild = self.bot.get_guild(self.bot.config["server_id"])

    @tasks.loop(minutes=5)
    async def update_events(self):
        """Fetches events from the calendar, does processing, and calls the appropriate handler."""

        for handler in self.handlers:
            with urllib.request.urlopen(handler.calendar_url) as u:
                ical_string = u.read()
            calendar = icalendar.Calendar.from_ical(ical_string)
            events = recurring_ical_events.of(calendar).between(
                datetime.now(),
                datetime.now() + timedelta(days=handler.delta_days),
            )

            scheduled_events = await self.guild.fetch_scheduled_events()
            for event in events:
                await self.handle_event(handler, event, scheduled_events)

    async def handle_event(
        self, handler: Handler, event: dict, scheduled_events: list[ScheduledEvent]
    ) -> None:
        """Does some common pre-processing before calling the handler."""

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

        if len(event_data["description"]) > 999:
            # event descriptions are max 1000 characters, API call will fail if passed
            # messages have limit of 2000, no need for separate check there
            event_data["description"] = event_data["description"][:995] + "..."
        if len(event_data["name"]) > 100:
            # event name are max 100 characters, API call will fail if passed
            event_data["name"] = event_data["name"][:95] + "..."

        scheduled_event = next(
            (e for e in scheduled_events if e.name == event_data["name"].rstrip()),
            None,
        )

        try:
            await handler.handle_event(self.guild, event_data, scheduled_event)
        except Exception:  # pylint: disable=broad-exception-caught
            logging.error(
                "Error in event %s:\n%s",
                event["SUMMARY"],
                traceback.format_exc(),
            )

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(
        self, event: ScheduledEvent, user: User
    ):  # pylint: disable=missing-function-docstring
        for handler in self.handlers:
            await handler.event_user_manage(event, user, True)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(
        self, event: ScheduledEvent, user: User
    ):  # pylint: disable=missing-function-docstring
        for handler in self.handlers:
            await handler.event_user_manage(event, user, False)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(
        self, event: ScheduledEvent
    ):  # pylint: disable=missing-function-docstring
        for handler in self.handlers:
            await handler.event_delete(event)

    @update_events.before_loop
    async def before_loop(self):
        """Ensures the bot is ready before the loop starts."""
        logging.info("running before_loop")
        await self.bot.wait_until_ready()


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Events(bot))
