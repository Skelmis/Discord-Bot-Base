import logging

from bot_base import BotBase
from bot_base.context import BotContext

try:
    import nextcord as discord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import disnake as discord
    from disnake.ext import commands

log = logging.getLogger(__name__)


class Internal(commands.Cog):
    def __init__(self, bot):
        self.bot: BotBase = bot

    def cog_check(self, ctx) -> bool:
        try:
            _exists = self.bot.blacklist
            return True
        except AttributeError:
            return False

    @commands.Cog.listener()
    async def on_initial_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    @commands.group(invoke_without_command=True)
    @commands.is_owner()
    async def blacklist(self, ctx: BotContext) -> None:
        """Top level blacklist interface"""
        await ctx.send_help(ctx.command)

    @blacklist.group(invoke_without_command=True)
    @commands.is_owner()
    async def add(self, ctx: BotContext) -> None:
        """Add something to the blacklist"""
        await ctx.send_help(ctx.command)

    @add.command(name="person")
    @commands.is_owner()
    async def add_person(
        self, ctx: BotContext, user: discord.Object, *, reason=None
    ) -> None:
        """Add someone to the blacklist"""
        await self.bot.blacklist.add_to_blacklist(
            user.id, reason=reason, is_guild_blacklist=False
        )
        await ctx.send_basic_embed(f"I have added <@{user.id}> to the blacklist.")

    @add.command(name="guild")
    @commands.is_owner()
    async def add_guild(
        self, ctx: BotContext, guild: discord.Object, *, reason=None
    ) -> None:
        await self.bot.blacklist.add_to_blacklist(
            guild.id, reason=reason, is_guild_blacklist=True
        )
        await ctx.send_basic_embed(
            f"I have added the guild `{guild.id}` to the blacklist"
        )

    @blacklist.command()
    @commands.is_owner()
    async def list(self, ctx: BotContext) -> None:
        """List all current blacklists"""
        if self.bot.blacklist.users:
            user_blacklists = "\n".join(f"`{u}`" for u in self.bot.blacklist.users)
        else:
            user_blacklists = "No user's blacklisted."

        if self.bot.blacklist.guilds:
            guild_blacklists = "\n".join(f"`{g}`" for g in self.bot.blacklist.guilds)
        else:
            guild_blacklists = "No guild's blacklisted."

        await ctx.send(
            embed=discord.Embed(
                title="Blacklists",
                description=f"Users:\n{user_blacklists}\n\nGuilds:\n{guild_blacklists}",
            )
        )

    @blacklist.group(invoke_without_command=True)
    @commands.is_owner()
    async def remove(self, ctx: BotContext) -> None:
        """Remove something from the blacklist"""
        await ctx.send_help(ctx.command)

    @remove.command(name="person")
    @commands.is_owner()
    async def remove_person(self, ctx: BotContext, user: discord.Object) -> None:
        """Remove a person from the blacklist.

        Does nothing if they weren't blacklisted.
        """
        await self.bot.blacklist.remove_from_blacklist(
            user.id, is_guild_blacklist=False
        )
        await ctx.send_basic_embed("I have completed that action for you.")

    @remove.command(name="guild")
    @commands.is_owner()
    async def remove_guild(self, ctx: BotContext, guild: discord.Object) -> None:
        """Remove a guild from the blacklist.

        Does nothing if they weren't blacklisted.
        """
        await self.bot.blacklist.remove_from_blacklist(
            guild.id, is_guild_blacklist=True
        )
        await ctx.send_basic_embed("I have completed that action for you.")


def setup(bot):
    bot.add_cog(Internal(bot))
