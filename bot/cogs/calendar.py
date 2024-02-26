""""This module sets up events in discord based on the calendar events

To automate the work of making events on discord for the hack&chills, this cog
checks the StudSec calendar and creates a matching event for a hack&chill listed
there.
"""

import urllib.request
from datetime import datetime, timedelta

import icalendar
import recurring_ical_events
from discord.ext import commands, tasks


class Calendar(commands.Cog, name="calendar"):
    """The class to manage calendar related integration stuff in the discord"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.update_events.start()  # pylint: disable=no-member

    @tasks.loop(minutes=1)
    async def update_events(self) -> None:
        """Checks the calendar, and adds/updates events if needed"""
        ical_string = urllib.request.urlopen(self.bot.config["calendar"]).read()
        calendar = icalendar.Calendar.from_ical(ical_string)

        current = datetime.now()
        events = recurring_ical_events.of(calendar).between(
            (current.year, current.month, current.day),
            (current.year, current.month, current.day + 3),
        )

        guild = self.bot.get_guild(self.bot.config["server_id"])
        if guild is None:
            return

        for event in events:
            if event["SUMMARY"] != "Meetup":
                continue

            for scheduled_event in await guild.fetch_scheduled_events():
                if scheduled_event.start_time == event["DTSTART"].dt:
                    return

            if event["DTSTART"].dt - timedelta(hours=3) < datetime.now(
                event["DTSTART"].dt.tzinfo
            ) or (
                event["DTSTART"].dt - timedelta(hours=48)
                > datetime.now(event["DTSTART"].dt.tzinfo)
            ):
                return

            event_link = await guild.create_scheduled_event(
                name="Hack&Chill",
                start_time=event["DTSTART"].dt,
                end_time=event["DTEND"].dt,
                location="NU, Vrije Universiteit",
                description="",
            )

            message = await self.bot.get_channel(
                self.bot.config["channel"]["announcements"]
            ).send(
                "\n".join(self.bot.config["hacknchill"]["message"]).format(
                    url=event_link.url
                )
            )

            await message.add_reaction("❌")

    @update_events.before_loop
    async def before_loop(self) -> None:
        """Make sure the bot is ready"""
        await self.bot.wait_until_ready()


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Calendar(bot))
