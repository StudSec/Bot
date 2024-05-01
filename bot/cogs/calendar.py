""""This module sets up events in discord based on the calendar events

To automate the work of making events on discord for the hack&chills and other events, this cog
checks the StudSec calendar and creates a matching event..
"""

import urllib.request
from datetime import datetime, timedelta, date

import logging
import traceback
import icalendar
import recurring_ical_events
from discord.ext import commands, tasks
from discord import EntityType, PrivacyLevel


class Calendar(commands.Cog, name="calendar"):
    """The class to manage calendar related integration stuff in the discord"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.update_events.start()  # pylint: disable=no-member

    @tasks.loop(minutes=1)
    async def update_events(self) -> None:
        """Checks the calendar, and adds/updates events if needed"""
        with urllib.request.urlopen(self.bot.config["events_calendar"]) as u:
            ical_string = u.read()
        calendar = icalendar.Calendar.from_ical(ical_string)

        current = datetime.now()
        future = date.today() + timedelta(days=10)
        events = recurring_ical_events.of(calendar).between(
            (current.year, current.month, current.day),
            (future.year, future.month, future.day),
        )

        guild = self.bot.get_guild(self.bot.config["server_id"])
        if guild is None:
            return

        scheduled_events = await guild.fetch_scheduled_events()
        for event in events:
            # NOTE: does not support dates, only events with set start and end times.
            try:
                for scheduled_event in await guild.fetch_scheduled_events():
                    if scheduled_event.start_time == event["DTSTART"].dt:
                        return

                if event["DTSTART"].dt - timedelta(hours=3) < datetime.now(
                    event["DTSTART"].dt.tzinfo
                ):
                    return

                # Fill in missing keys
                description = str(event.get("DESCRIPTION", ""))
                location = str(event.get("LOCATION", ""))

                for scheduled_event in scheduled_events:
                    if scheduled_event.name == event["SUMMARY"]:
                        # Update info to make sure it matches
                        await scheduled_event.edit(
                            name=event["SUMMARY"],
                            start_time=event["DTSTART"].dt,
                            end_time=event["DTEND"].dt,
                            location=location,
                            description=description,
                            entity_type=EntityType.external,
                            privacy_level=PrivacyLevel.guild_only,
                        )
                        break
                else:
                    event_link = await guild.create_scheduled_event(
                        name=event["SUMMARY"],
                        start_time=event["DTSTART"].dt,
                        end_time=event["DTEND"].dt,
                        location=location,
                        description=description,
                        entity_type=EntityType.external,
                        privacy_level=PrivacyLevel.guild_only,
                    )

                    message = await self.bot.get_channel(
                        self.bot.config["channel"]["announcements"]
                    ).send(
                        "\n".join(
                            self.bot.config["calendar_announcement"]["message"]
                        ).format(
                            title=event["SUMMARY"],
                            date=event["DTSTART"].dt.strftime("%H:%M %d/%m/%Y"),
                            url=event_link.url,
                            description=description,
                        )
                    )

                    await message.add_reaction("❌")
            except Exception:  # pylint: disable=broad-exception-caught
                logging.error(
                    "Error in calendar event %s:\n%s",
                    event["SUMMARY"],
                    traceback.format_exc(),
                )

    @update_events.before_loop
    async def before_loop(self) -> None:
        """Make sure the bot is ready"""
        await self.bot.wait_until_ready()


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(Calendar(bot))
