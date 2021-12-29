try:
    import nextcord as discord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import discord
    from discord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedUser(Meta, discord.User):
    """Wraps discord.user for ease of stuff"""

    def __init__(self, person: discord.User, bot):
        self.person: discord.User = person
        self._bot = bot

    @classmethod
    async def convert(cls, ctx, argument: str) -> "WrappedUser":
        user: discord.User = await commands.UserConverter().convert(
            ctx=ctx, argument=argument
        )
        return cls(user, ctx.bot)

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from author itself"""
        return getattr(self.person, item)

    @property
    def __class__(self):
        return type(self.person)

    def __eq__(self, other) -> bool:
        if not isinstance(other, (type(self.person), WrappedUser)):
            return False

        if isinstance(other, type(self.person)):
            return other.id == self.person.id

        return other.person.id == self.person.id

    def __hash__(self):
        return hash(self.person)
