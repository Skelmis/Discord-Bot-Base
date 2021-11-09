import datetime
import sys
import logging
import traceback
from typing import Optional, List

import discord
import humanize

try:
    from nextcord import DiscordException
    from nextcord.ext import commands
except ModuleNotFoundError:
    from discord import DiscordException
    from discord.ext import commands

from bot_base.blacklist import BlacklistManager
from bot_base.context import BotContext
from bot_base.db import MongoManager
from bot_base.exceptions import PrefixNotFound
from bot_base.wraps import (
    WrappedChannel,
    WrappedMember,
    WrappedChannelConvertor,
    WrappedMemberConvertor,
    WrappedUserConvertor,
    WrappedUser,
)

log = logging.getLogger(__name__)

try:
    from nextcord.ext.commands.converter import CONVERTER_MAPPING

    CONVERTER_MAPPING[discord.User] = WrappedUserConvertor
    CONVERTER_MAPPING[discord.Member] = WrappedMemberConvertor
    CONVERTER_MAPPING[discord.TextChannel] = WrappedChannelConvertor
except ModuleNotFoundError:
    raise RuntimeWarning(
        "You don't have overridden converters. Please open an issue and name the fork your using."
    )


class BotBase(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        self.db: MongoManager = MongoManager(
            kwargs.pop("mongo_url"), kwargs.pop("mongo_database_name", None)
        )
        self.blacklist: BlacklistManager = BlacklistManager(self.db)
        self._uptime: datetime.datetime = datetime.datetime.now(
            tz=datetime.timezone.utc
        )

        self.DEFAULT_PREFIX: str = kwargs.get("command_prefix")  # type: ignore

        super().__init__(*args, **kwargs)

    @property
    def uptime(self) -> datetime.datetime:
        return self._uptime

    def get_bot_uptime(self) -> str:
        return humanize.precisedelta(
            self.uptime - datetime.datetime.now(tz=datetime.timezone.utc)
        )

    async def on_ready(self) -> None:
        await self.blacklist.initialize()

    async def get_command_prefix(self, message: discord.Message) -> List[str]:
        try:
            prefix = await self.get_guild_prefix(guild_id=message.guild.id)

            if message.content.casefold().startswith(prefix.casefold()):
                # The prefix matches, now return the one the user used
                # such that dpy will dispatch the given command
                prefix_length = len(prefix)
                prefix = message.content[:prefix_length]

            return commands.when_mentioned_or(prefix)(self, message)

        except (AttributeError, PrefixNotFound):
            return commands.when_mentioned_or(self.DEFAULT_PREFIX)(self, message)

    # TODO Add caching
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
        prefix_data = self.db.config.find(guild_id)

        if not prefix_data:
            raise PrefixNotFound

        prefix: Optional[str] = prefix_data.get("prefix")
        if not prefix:
            raise PrefixNotFound

        return prefix

    async def on_command_error(self, ctx: BotContext, error: DiscordException) -> None:
        error = getattr(error, "original", error)

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.author.send("This command cannot be used in private messages.")
        elif isinstance(error, commands.DisabledCommand):
            await ctx.author.send("Sorry. This command is disabled and cannot be used.")
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if not isinstance(original, discord.HTTPException):
                print(f"In {ctx.command.qualified_name}:", file=sys.stderr)
                traceback.print_tb(original.__traceback__)
                print(f"{original.__class__.__name__}: {original}", file=sys.stderr)
        elif isinstance(error, commands.ArgumentParsingError):
            await ctx.send(error)
        elif isinstance(error, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in dm's.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("This command can only be used in Guilds.")

        if not isinstance(error, commands.CommandNotFound):
            if await self.db.command_usage.find(ctx.command.qualified_name) is None:
                await self.db.command_usage.upsert(
                    {
                        "_id": ctx.command.qualified_name,
                        "usage_count": 0,
                        "failure_count": 1,
                    }
                )
            else:
                await self.db.command_usage.increment(
                    ctx.command.qualified_name, 1, "failure_count"
                )

            log.debug(f"Command failed: `{ctx.command.qualified_name}`")
        raise error

    async def on_command_completion(self, ctx: BotContext) -> None:
        if ctx.command.qualified_name == "logout":
            return

        if await self.db.command_usage.find(ctx.command.qualified_name) is None:
            await self.db.command_usage.upsert(
                {
                    "_id": ctx.command.qualified_name,
                    "usage_count": 1,
                    "failure_count": 0,
                }
            )
        else:
            await self.db.command_usage.increment(
                ctx.command.qualified_name, 1, "usage_count"
            )
        log.debug(f"Command executed: `{ctx.command.qualified_name}`")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        if guild.id in self.blacklist.guilds:
            await guild.leave()

    async def process_commands(self, message: discord.Message) -> None:
        ctx = await self.get_context(message, cls=BotContext)

        if ctx.author.id in self.blacklist.users:
            log.debug(f"Ignoring blacklisted user: {ctx.author.id}")
            return

        if ctx.guild is not None and ctx.guild.id in self.blacklist.guilds:
            log.debug(f"Ignoring blacklisted guild: {ctx.guild.id}")
            return

        await self.invoke(ctx)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        await self.process_commands(message)

    async def get_or_fetch_member(self, guild_id: int, member_id: int) -> WrappedMember:
        """Looks up a member in cache or fetches if not found."""
        guild = await self.get_or_fetch_guild(guild_id)
        member = guild.get_member(member_id)
        if member is not None:
            return WrappedMember(member)

        member = await guild.fetch_member(member_id)
        return WrappedMember(member)

    async def get_or_fetch_channel(self, channel_id: int) -> WrappedChannel:
        """Looks up a channel in cache or fetches if not found."""
        channel = self.get_channel(channel_id)
        if channel:
            return WrappedChannel(channel)

        channel = await self.fetch_channel(channel_id)
        return WrappedChannel(channel)

    async def get_or_fetch_guild(self, guild_id: int) -> discord.Guild:
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
            return WrappedUser(user)

        user = await self.fetch_user(user_id)
        return WrappedUser(user)
