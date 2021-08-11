import sys
import traceback
from typing import List

import discord
from discord.ext import commands

from bot_base.db import MongoManager
from bot_base.exceptions import PrefixNotFound


class BotBase(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.db = MongoManager(kwargs.pop("mongo_url"))
        self.DEFAULT_PREFIX = kwargs.pop("default_prefix")

        super().__init__(*args, **kwargs)

    async def get_command_prefix(self, message):
        try:
            prefix = await self.get_guild_prefix(guild_id=message.guild.id)
            return commands.when_mentioned_or(prefix)(self, message)

        except (AttributeError, PrefixNotFound):
            return commands.when_mentioned_or(self.DEFAULT_PREFIX)(self, message)

    # TODO Add caching
    async def get_guild_prefix(self, guild_id: int = None) -> str:
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
        prefix = self.db.config.find(guild_id)

        if not prefix:
            raise PrefixNotFound

        return prefix

    async def on_command_error(self, ctx, error):
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
