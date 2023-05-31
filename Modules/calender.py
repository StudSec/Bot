"""
Queries the studsec google calendar to announce scheduled meetups.
"""
# Custom imports
from . import registry

# External imports
import discord
import asyncio
import icalendar
import urllib.request
import recurring_ical_events
from discord.ext import tasks
from datetime import datetime, timedelta


url = "https://calendar.google.com/calendar/ical/c_1e4d18d298e5a27f2d7fb0cb5ca4f3791ae3db284a80996ee5346894d9f210b4%40group.calendar.google.com/public/basic.ics"
announcment_message = """<@&1080528650140647454> we have another hack & chill planned this Thursday! The plan is to meetup, socialize and hack together. If your interested in coming, join the discord event!

The meetup is scheduled for 1900 in NU. If you can't/won't make it, react with ❌

{url}
"""
cancel_message = "This weeks Hack&Chill has been cancelled, less than 3 people could make it :/"
server_id = 880765355935535165
announcement_channel = 881230276049633360
# Debug channel info
# server_id = 981278603528523866
# announcement_channel = 981280566894805042


class HacknChill:
    def __init__(self, client):
        self.commands = {
        }
        self.name = ["Hack&Chill"]
        self.category = ["Social"]
        self.client = client
        self.type = "Runtime"
        self.update_events.start()

    async def process_message(self, message):
        pass

    @tasks.loop()
    async def update_events(self):
        await asyncio.sleep(60)
        start = datetime.now()
        end = start + timedelta(days=3)
        ical_string = urllib.request.urlopen(url).read()
        calendar = icalendar.Calendar.from_ical(ical_string)
        events = recurring_ical_events.of(calendar).between(
            (start.year, start.month, start.day),
            (end.year, end.month, end.day)
        )
        for event in events:
            if event["SUMMARY"] != "Meetup":
                continue
            # Check if event exists
            for scheduled_event in await self.client.get_guild(server_id).fetch_scheduled_events():
                if scheduled_event.start_time == event["DTSTART"].dt:
                    return

            # Check if event is closer than 3 hours
            if event["DTSTART"].dt - timedelta(hours=3) < datetime.now(event["DTSTART"].dt.tzinfo):
                return

            # Check if event is farther away than 48 hours
            if event["DTSTART"].dt - timedelta(hours=48) > datetime.now(event["DTSTART"].dt.tzinfo):
                return

            # If not make event
            event_link = await self.client.get_guild(server_id).create_scheduled_event(name="Hack&Chill",
                                                                                       start_time=event["DTSTART"].dt,
                                                                                       end_time=event["DTEND"].dt,
                                                                                       location="NU, Vrije Universiteit",
                                                                                       description="")

            # And send message
            await self.client.get_channel(announcement_channel).send(announcment_message.format(url=event_link.url)
                                                                     ).add_reaction("❌")


registry.register(HacknChill)
