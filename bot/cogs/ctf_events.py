""""This module sets up CTF events in discord based on the calendar events
"""

import urllib.request
from datetime import datetime, timedelta

import pytz
import icalendar
import recurring_ical_events
from discord.ext import commands, tasks
from discord import EntityType, PrivacyLevel, PermissionOverwrite


class CTFEvents(commands.Cog, name="ctf_events"):
    """The class to manage calendar related integration stuff in the discord"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.update_events.start()  # pylint: disable=no-member

    @tasks.loop(minutes=1)
    async def update_events(self) -> None:
        """Checks the calendar, and adds/updates events if needed"""
        ical_string = urllib.request.urlopen(self.bot.config["ctf_calendar"]).read()
        calendar = icalendar.Calendar.from_ical(ical_string)

        current = datetime.now()
        timezone = pytz.timezone('Europe/Amsterdam')
        events = recurring_ical_events.of(calendar).between(
            (current.year, current.month, current.day),
            (current.year, current.month, current.day + 10),
        )

        guild = self.bot.get_guild(self.bot.config["server_id"])
        if guild is None:
            return

        scheduled_events = await guild.fetch_scheduled_events()

        for event in events:
            # Fill in missing keys
            description = str(event.get("DESCRIPTION", ""))
            location = str(event.get("LOCATION", ""))


            for scheduled_event in scheduled_events:
                if scheduled_event.name == event["SUMMARY"]:
                    # This is a bit of a conflict, in the calendar we just want the days of the event to be marked off, especially because its a multi-day event. But the event itself we might want to manually update
                    # the times. Because of this, we don't make the event editable after creation.
                    
                    # Update roles
                    for channel_category, channel_list in guild.by_category():
                        if channel_category and channel_category.name == f"CTFs - {event['DTSTART'].dt.strftime('%Y')}":
                            for channel in channel_list:
                                if channel.name == event["SUMMARY"].replace(" ", "-").lower():
                                    async for user in scheduled_event.users():
                                        await channel.set_permissions(user, read_messages=True)
                                    break
                    break
            else:
                
                event_link = await guild.create_scheduled_event(
                    name=event["SUMMARY"],
                    start_time=timezone.localize(datetime.combine(event["DTSTART"].dt, datetime.min.time())),
                    end_time=timezone.localize(datetime.combine(event["DTEND"].dt, datetime.min.time())),
                    location=location,
                    description=description,
                    entity_type=EntityType.external,
                    privacy_level=PrivacyLevel.guild_only
                )

                for channel_category, channel_list in guild.by_category():
                    if channel_category and channel_category.name == f"CTFs - {event['DTSTART'].dt.strftime('%Y')}":
                        category = channel_category
                        break
                else:
                    category = await guild.create_category(f"CTFs - {event['DTSTART'].dt.strftime('%Y')}")

                overwrites = {
                    guild.default_role: PermissionOverwrite(read_messages=False),
                }

                forum = await category.create_forum(event["SUMMARY"], overwrites=overwrites)
                init_post = await forum.create_thread(name="General", content=f"General discussion thread for {event['SUMMARY']}")

                # This method only works for messages, to my knowledge there is currently no way to pin forums threads - Aidan                
                # await init_post.pin()
                
                # Add tags, this can be done in the forum creation but this is more readable.
                await forum.create_tag(name="busy")
                await forum.create_tag(name="done")
                await forum.create_tag(name="stuck")

    @update_events.before_loop
    async def before_loop(self) -> None:
        """Make sure the bot is ready"""
        await self.bot.wait_until_ready()


async def setup(bot) -> None:  # pylint: disable=missing-function-docstring
    await bot.add_cog(CTFEvents(bot))
