"""This module implements the Handler classes, which handle events of a specific type."""

from __future__ import annotations
import logging
import sqlite3

from datetime import datetime, timedelta
from discord import Guild, ScheduledEvent, User, PermissionOverwrite, EntityType
from discord.channel import ForumChannel


class Handler:
    """A base class that represents the handler for a specific event type."""

    def __init__(self, bot, calendar_url: str, event_type: str, delta_days: int):
        self.bot = bot
        self.event_type = event_type
        self.calendar_url = calendar_url
        self.delta_days = delta_days

    async def handle_event(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """Handles events by creating and updating Discord events."""
        raise NotImplementedError

    async def event_user_manage(self, event: ScheduledEvent, user: User, read: bool):
        """Manages users being added or removed from a channel"""

    async def event_delete(self, event: ScheduledEvent):
        """Deletes an event"""

    @staticmethod
    def get_handlers(bot) -> list[Handler]:
        """Return a list of all Handler instances for the bot."""
        return [
            CTFHandler(bot, bot.config["ctf"]["calendar"]),
            CalendarHandler(bot, bot.config["cal"]["calendar"]),
        ]


class CTFHandler(Handler):
    """A class that represents the handler for CTF events."""

    def __init__(self, bot, calendar_url: str, event_type="CTF", delta_days=30):
        super().__init__(bot, calendar_url, event_type, delta_days)

    async def handle_event(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """Handles CTF-specific events by creating and updating Discord events and channels."""
        if not scheduled_event:
            # This is a bit of a conflict, in the calendar we just want the days of
            # the event to be marked off, especially because its a multi-day event.
            # But the event itself we might want to manually update the times.
            # Because of this, we don't make the event editable after creation.

            await guild.create_scheduled_event(**event_data)
            logging.info("Created CTF event for %s", event_data["name"])

            for channel_category, _ in guild.by_category():
                if (
                    channel_category
                    and channel_category.name
                    == f"CTFs - {event_data['start_time'].strftime('%Y')}"
                ):
                    category = channel_category
                    break
            else:
                category = await guild.create_category(
                    f"CTFs - {event_data['start_time'].strftime('%Y')}"
                )

            if event_data["name"].lower().replace(" ", "-") in [
                f.name for f in category.forums
            ]:
                # there already is a forum for this
                return

            overwrites = {
                guild.default_role: PermissionOverwrite(read_messages=False),
            }
            forum = await category.create_forum(
                event_data["name"], overwrites=overwrites
            )

            await forum.create_thread(
                name="General",
                content=f"General discussion thread for {event_data['name']}",
            )
            logging.info("Created CTF forum for %s", event_data["name"])

            # Add tags, this can be done in the forum creation but this is more readable.
            await forum.create_tag(name="busy")
            await forum.create_tag(name="done")
            await forum.create_tag(name="stuck")

    async def event_user_manage(self, event: ScheduledEvent, user: User, read):
        """Manages users being added or removed from a channel"""
        if not event.guild:
            return

        for category, channels in event.guild.by_category():
            if (
                not category
                or category.name != f"CTFs - {event.start_time.strftime('%Y')}"
            ):
                continue

            if forum := next(
                (c for c in channels if c.name == event.name.replace(" ", "-").lower()),
                None,
            ):
                if not isinstance(forum, ForumChannel):
                    continue

                await forum.set_permissions(user, read_messages=read)  # type: ignore
                if (
                    general := next(
                        (t for t in forum.threads if t.name == "General"), None
                    )
                ) and read:
                    await general.add_user(user)

                logging.info(
                    "%s %s to CTF %s",
                    ("Added" if read else "Removed"),
                    user.name,
                    event.name,
                )


class CalendarHandler(Handler):
    """A class that represents the handler for calendar events."""

    def __init__(self, bot, calendar_url: str, event_type="Calendar", delta_days=11):
        super().__init__(bot, calendar_url, event_type, delta_days)

    @staticmethod
    def format_announcement(config: dict, event_data: dict, url: str) -> str:
        """Formats the announcement message with the needed data"""
        return "\n".join(config["cal"]["announcement"]).format(
            title=event_data["name"],
            date=event_data["start_time"].strftime("%H:%M %d/%m/%Y"),
            url=url,
            description=event_data["description"],
        )

    async def handle_event(
        self, guild: Guild, event_data: dict, scheduled_event: ScheduledEvent
    ):
        """Handles calendar events by creating and updating Discord events, possibly a preview."""
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

    async def _handle_existing_event(
        self,
        guild: Guild,
        event_data: dict,
        scheduled_event: ScheduledEvent,
        channel,
    ):
        """Handles existing events by updating or deleting them"""
        with sqlite3.connect(f"{self.bot.shared}/events.db") as conn:
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
            with sqlite3.connect(f"{self.bot.shared}/events.db") as conn:
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
        reaction = None

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

        if reaction:
            await message.add_reaction(reaction)

        with sqlite3.connect(f"{self.bot.shared}/events.db") as conn:
            conn.execute(
                "INSERT INTO events (event_id, message_id, is_preview) VALUES (?, ?, ?)",
                (
                    event.id,
                    message.id,
                    1 if channel.name in self.bot.config["private"]["channels"] else 0,
                ),
            )

        logging.info("Created event %s in %s", event_data["name"], channel.name)

    async def event_delete(self, event: ScheduledEvent):
        """Deletes an event"""
        with sqlite3.connect(f"{self.bot.shared}/events.db") as conn:
            conn.execute("DELETE FROM events WHERE event_id = ?", (event.id,))
        logging.info("Deleted event %s", event.name)
