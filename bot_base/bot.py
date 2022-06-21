import datetime
import sys
import logging
import traceback
from typing import Optional, List, Any, Dict, Union, Callable

import humanize
from alaric import AQ
from alaric.comparison import EQ

from bot_base import CancellableWaitFor
from bot_base.caches import TimedCache

try:
    import nextcord
    from nextcord import DiscordException, abc
    from nextcord.ext import commands
    from nextcord.ext.commands.converter import CONVERTER_MAPPING
except ModuleNotFoundError:
    import disnake as nextcord
    from disnake import DiscordException, abc
    from disnake.ext import commands
    from disnake.ext.commands.converter import CONVERTER_MAPPING

from bot_base.blacklist import BlacklistManager
from bot_base.context import BotContext
from bot_base.db import MongoManager
from bot_base.exceptions import PrefixNotFound, BlacklistedEntry
from bot_base.wraps import (
    WrappedChannel,
    WrappedMember,
    WrappedUser,
    WrappedThread,
)

log = logging.getLogger(__name__)


CONVERTER_MAPPING[nextcord.User] = WrappedUser
CONVERTER_MAPPING[nextcord.Member] = WrappedMember
CONVERTER_MAPPING[nextcord.TextChannel] = WrappedChannel


class BotBase(commands.Bot):
    def __init__(
        self,
        *args,
        mongo_url: str,
        command_prefix: str,
        leave_db: bool = False,
        do_command_stats: bool = True,
        load_builtin_commands: bool = False,
        mongo_database_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        if not leave_db:
            self.db: MongoManager = MongoManager(mongo_url, mongo_database_name)

        self.do_command_stats: bool = do_command_stats
        try:
            self.blacklist: BlacklistManager = BlacklistManager(self.db)
        except AttributeError:
            log.warning(
                "You do not have a blacklist setup. "
                "Please set `self.db` to a instance/subclass of MongoManager before "
                "calling (..., leave_db=True) if you wish to have a blacklist."
            )
            self.blacklist = None

        self._uptime: datetime.datetime = datetime.datetime.now(
            tz=datetime.timezone.utc
        )
        self.prefix_cache: TimedCache = TimedCache()

        self.DEFAULT_PREFIX: str = command_prefix
        kwargs["command_prefix"] = self.get_command_prefix

        super().__init__(*args, **kwargs)

        if load_builtin_commands:
            self.load_extension("bot_base.cogs.internal")

        # These events do include the on_ prefix
        self._single_event_type_sheet: Dict[str, Callable] = {
            "on_message": self.get_wrapped_message,
        }
        self._double_event_type_sheet: Dict[str, Callable] = {
            "on_message_edit": lambda before, after: (
                self.get_wrapped_message(before),
                self.get_wrapped_message(after),
            )
        }

    @property
    def uptime(self) -> datetime.datetime:
        return self._uptime

    def get_uptime(self) -> str:
        return humanize.precisedelta(
            self.uptime - datetime.datetime.now(tz=datetime.timezone.utc)
        )

    def get_bot_uptime(self) -> str:
        log.warning("This method is deprecated, use get_uptime instead")
        return self.get_uptime()

    async def on_ready(self) -> None:
        if self.blacklist:
            await self.blacklist.initialize()

    async def get_command_prefix(
        self, bot: "BotBase", message: nextcord.Message
    ) -> List[str]:
        try:
            prefix = await self.get_guild_prefix(guild_id=message.guild.id)

            prefix = self.get_case_insensitive_prefix(message.content, prefix)

            return commands.when_mentioned_or(prefix)(self, message)

        except (AttributeError, PrefixNotFound):
            prefix = self.get_case_insensitive_prefix(
                message.content, self.DEFAULT_PREFIX
            )
            return commands.when_mentioned_or(prefix)(self, message)

    @staticmethod
    def get_case_insensitive_prefix(content, prefix):
        if content.casefold().startswith(prefix.casefold()):
            # The prefix matches, now return the one the user used
            # such that dpy will dispatch the given command
            prefix_length = len(prefix)
            prefix = content[:prefix_length]

        return prefix

    async def get_guild_prefix(self, guild_id: Optional[int] = None) -> str:
        """
        Using a cached property fetch prefixes
        for a guild and return em.

        Parameters
        ----------
        guild_id : int
            The guild we want prefixes for

        Returns
        -------
        str
            The prefix

        Raises
        ------
        PrefixNotFound
            We failed to find and
            return a valid prefix
        """
        if guild_id in self.prefix_cache:
            return self.prefix_cache.get_entry(guild_id)

        prefix_data = await self.db.config.find({"_id": guild_id})

        if not prefix_data:
            raise PrefixNotFound

        prefix: Optional[str] = prefix_data.get("prefix")
        if not prefix:
            raise PrefixNotFound

        self.prefix_cache.add_entry(guild_id, prefix, override=True)
        return prefix

    async def on_command_error(self, ctx: BotContext, error: DiscordException) -> None:
        error = getattr(error, "original", error)

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, nextcord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You do not have permissions to run this command.")
        elif isinstance(error, BlacklistedEntry):
            await ctx.send(error.message)

        if not isinstance(error, commands.CommandNotFound) and self.do_command_stats:
            if (
                await self.db.command_usage.find(
                    AQ(EQ("_id", ctx.command.qualified_name))
                )
                is None
            ):
                await self.db.command_usage.upsert(
                    AQ(EQ("_id", ctx.command.qualified_name)),
                    {
                        "_id": ctx.command.qualified_name,
                        "usage_count": 0,
                        "failure_count": 1,
                    },
                )
            else:
                await self.db.command_usage.increment(
                    AQ(EQ("_id", ctx.command.qualified_name)), 1, "failure_count"
                )

            log.debug(f"Command failed: `{ctx.command.qualified_name}`")
        raise error

    async def on_command_completion(self, ctx: BotContext) -> None:
        if ctx.command.qualified_name == "logout":
            return

        if self.do_command_stats:
            if (
                await self.db.command_usage.find(
                    AQ(EQ("_id", ctx.command.qualified_name))
                )
                is None
            ):
                await self.db.command_usage.upsert(
                    AQ(EQ("_id", ctx.command.qualified_name)),
                    {
                        "_id": ctx.command.qualified_name,
                        "usage_count": 1,
                        "failure_count": 0,
                    },
                )
            else:
                await self.db.command_usage.increment(
                    AQ(EQ("_id", ctx.command.qualified_name)), 1, "usage_count"
                )
        log.debug(f"Command executed: `{ctx.command.qualified_name}`")

    async def on_guild_join(self, guild: nextcord.Guild) -> None:
        if self.blacklist and guild.id in self.blacklist.guilds:
            log.info("Leaving blacklisted Guild(id=%s)", guild.id)
            await guild.leave()

    async def process_commands(self, message: nextcord.Message) -> None:
        ctx = await self.get_context(message, cls=BotContext)

        if self.blacklist and ctx.author.id in self.blacklist.users:
            log.debug(f"Ignoring blacklisted user: {ctx.author.id}")
            raise BlacklistedEntry(f"Ignoring blacklisted user: {ctx.author.id}")

        if (
            self.blacklist
            and ctx.guild is not None
            and ctx.guild.id in self.blacklist.guilds
        ):
            log.debug(f"Ignoring blacklisted guild: {ctx.guild.id}")
            raise BlacklistedEntry(f"Ignoring blacklisted guild: {ctx.guild.id}")

        if ctx.command:
            log.debug(
                "Invoked command %s for User(id=%s)",
                ctx.command.qualified_name,
                ctx.author.id,
            )

        await self.invoke(ctx)

    async def on_message(self, message: nextcord.Message) -> None:
        if message.author.bot:
            log.debug("Ignoring a message from a bot.")
            return

        await self.process_commands(message)

    async def get_or_fetch_member(self, guild_id: int, member_id: int) -> WrappedMember:
        """Looks up a member in cache or fetches if not found."""
        guild = await self.get_or_fetch_guild(guild_id)
        member = guild.get_member(member_id)
        if member is not None:
            return WrappedMember(member, bot=self)

        member = await guild.fetch_member(member_id)
        return WrappedMember(member, bot=self)

    async def get_or_fetch_channel(self, channel_id: int) -> WrappedChannel:
        """Looks up a channel in cache or fetches if not found."""
        channel = self.get_channel(channel_id)
        if channel:
            return self.get_wrapped_channel(channel)

        channel = await self.fetch_channel(channel_id)
        return self.get_wrapped_channel(channel)

    async def get_or_fetch_guild(self, guild_id: int) -> nextcord.Guild:
        """Looks up a guild in cache or fetches if not found."""
        guild = self.get_guild(guild_id)
        if guild:
            return guild

        guild = await self.fetch_guild(guild_id)
        return guild

    async def get_or_fetch_user(self, user_id: int) -> WrappedUser:
        """Looks up a user in cache or fetches if not found."""
        user = self.get_user(user_id)
        if user:
            return WrappedUser(user, bot=self)

        user = await self.fetch_user(user_id)
        return WrappedUser(user, bot=self)

    def get_wrapped_channel(
        self,
        channel: Union[abc.GuildChannel, abc.PrivateChannel, nextcord.Thread],
    ) -> Union[WrappedThread, WrappedChannel]:
        if isinstance(channel, nextcord.Thread):
            return WrappedThread(channel, self)

        return WrappedChannel(channel, self)

    def get_wrapped_person(
        self, person: Union[nextcord.User, nextcord.Member]
    ) -> Union[WrappedUser, WrappedMember]:
        if isinstance(person, nextcord.Member):
            return WrappedMember(person, self)

        return WrappedUser(person, self)

    def get_wrapped_message(self, message: nextcord.Message) -> nextcord.Message:
        """
        Wrap the relevant params in message with meta classes.

        These fields are:
        message.channel: Union[WrappedThread, WrappedChannel]
        message.author: Union[WrappedUser, WrappedMember]
        """
        message.channel = self.get_wrapped_channel(message.channel)
        message.author = self.get_wrapped_person(message.author)

        return message

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        _name = f"on_{event_name}"
        # If we know the event, dispatch the wrapped one
        if _name in self._single_event_type_sheet:
            wrapped_arg = self._single_event_type_sheet[_name](args[0])
            super().dispatch(event_name, wrapped_arg)  # type: ignore

        elif _name in self._double_event_type_sheet:
            wrapped_first_arg, wrapped_second_arg = self._double_event_type_sheet[
                _name
            ](args[0], args[1])
            super().dispatch(event_name, wrapped_first_arg, wrapped_second_arg, self)

        else:
            super().dispatch(event_name, *args, **kwargs)  # type: ignore

    def cancellable_wait_for(
        self, event: str, *, check=None, timeout: int = None
    ) -> CancellableWaitFor:
        return CancellableWaitFor(self, event=event, check=check, timeout=timeout)
