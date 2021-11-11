import logging

from bot_base import BotBase
from bot_base.context import BotContext

try:
    import nextcord as discord
    from nextcord.ext import commands # noqa
except ModuleNotFoundError:
    import discord
    from discord.ext import commands # noqa

log = logging.getLogger(__name__)

class Internal(commands.Cog):
    def __init__(self, bot):
        self.bot: BotBase = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    @commands.group(invoke_without_command=True)
    async def blacklist(self, ctx: BotContext) -> None:
        """Top level blacklist interface"""
        await ctx.send_help(ctx.command)

    @commands.group(invoke_without_command=True)
    async def add(self, ctx: BotContext) -> None:
        """Add something to the blacklist"""
        await ctx.send_help(ctx.command)

    @add.command()
    async def person(self, ctx: BotContext, user: discord.Object, *, reason=None) -> None:
        """Add someone to the blacklist"""
        await self.bot.blacklist.add_to_blacklist(
            user.id,
            reason=reason,
            is_guild_blacklist=False
        )
        await ctx.send_basic_embed(f"I have added <@{user.id}> to the blacklist.")

    @add.command()
    async def guild(self, ctx: BotContext, guild: discord.Object, *, reason=None) -> None:
        await self.bot.blacklist.add_to_blacklist(
            guild.id,
            reason=reason,
            is_guild_blacklist=True
        )
        await ctx.send_basic_embed(f"I have added the guild `{guild.id}` to the blacklist")

    @blacklist.group()
    async def remove(self, ctx: BotContext) -> None:
        """Remove something from the blacklist"""
        await ctx.send_help(ctx.command)

    @remove.command()
    async def person(self, ctx: BotContext, user: discord.Object) -> None:
        """Remove a person from the blacklist.

        Does nothing if they weren't blacklisted.
        """
        await self.bot.blacklist.remove_from_blacklist(user.id, is_guild_blacklist=False)
        await ctx.send_basic_embed("I have completed that action for you.")

    @remove.command()
    async def guild(self, ctx: BotContext, guild: discord.Object) -> None:
        """Remove a guild from the blacklist.

        Does nothing if they weren't blacklisted.
        """
        await self.bot.blacklist.remove_from_blacklist(guild.id, is_guild_blacklist=True)
        await ctx.send_basic_embed("I have completed that action for you.")


def setup(bot):
    bot.add_cog(Internal(bot))