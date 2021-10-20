from typing import Any

import nextcord
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedMember(Meta, nextcord.Member):
    """Wraps nextcord.Member for ease of stuff"""

    def __init__(self, person: nextcord.Member) -> None:
        self.person: nextcord.Member = person

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from author itself"""
        return getattr(self.person, item)

    @property
    def __class__(self):
        return type(self.person)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (type(self.person), WrappedMember)):
            return False

        if isinstance(other, type(self.person)):
            return other.id == self.person.id

        return other.person.id == self.person.id


class WrappedMemberConvertor(commands.MemberConverter):
    """Return WrappedMember on :nextcord.Member"""

    async def convert(self, ctx, argument: str) -> WrappedMember:
        member: nextcord.Member = await super().convert(ctx=ctx, argument=argument)
        return WrappedMember(member)
