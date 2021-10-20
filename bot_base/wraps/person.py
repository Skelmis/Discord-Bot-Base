from typing import Union

import nextcord
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedPerson(Meta):
    """Wraps nextcord.Member, nextcord.User for ease of stuff"""

    def __init__(self, person: Union[nextcord.User, nextcord.Member]):
        self.person = person

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from author itself"""
        return getattr(self.person, item)

    @property
    def __class__(self):
        return type(self.person)

    def __eq__(self, other):
        if not isinstance(other, (type(self.person), WrappedPerson)):
            return False

        if isinstance(other, type(self.person)):
            return other.id == self.person.id

        return other.person.id == self.person.id


class WrappedMemberConvertor(commands.MemberConverter):
    """Return WrappedPerson on :nextcord.Member"""

    async def convert(self, ctx, argument: str) -> WrappedPerson:
        member: nextcord.Member = await super().convert(ctx=ctx, argument=argument)
        return WrappedPerson(member)


class WrappedUserConvertor(commands.UserConverter):
    """Return WrappedPerson on :nextcord.User"""

    async def convert(self, ctx, argument: str) -> WrappedPerson:
        user: nextcord.User = await super().convert(ctx=ctx, argument=argument)
        return WrappedPerson(user)
