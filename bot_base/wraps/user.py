import nextcord
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedUser(Meta, nextcord.User):
    """Wraps nextcord.user for ease of stuff"""

    def __init__(self, person: nextcord.User):
        self.person: nextcord.User = person

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
    """Return WrappedUser on :nextcord.User"""

    async def convert(self, ctx, argument: str) -> WrappedUser:
        user: nextcord.User = await super().convert(ctx=ctx, argument=argument)
        return WrappedUser(user)
