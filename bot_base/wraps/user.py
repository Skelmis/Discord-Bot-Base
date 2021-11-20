try:
    import nextcord as discord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import discord
    from discord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedUser(Meta, discord.User):
    """Wraps discord.user for ease of stuff"""

    def __init__(self, person: discord.User):
        self.person: discord.User = person

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


class WrappedUserConvertor(commands.UserConverter):
    """Return WrappedUser on :discord.User"""

    async def convert(self, ctx, argument: str) -> WrappedUser:
        user: discord.User = await super().convert(ctx=ctx, argument=argument)
        return WrappedUser(user)
