from typing import Any

try:
    import nextcord as discord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import discord
    from discord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedMember(Meta, discord.Member):
    """Wraps discord.Member for ease of stuff"""

    def __init__(self, person: discord.Member, bot) -> None:
        self.person: discord.Member = person
        self._bot = bot

    @classmethod
    async def convert(cls, ctx, argument: str) -> "WrappedMember":
        member: discord.Member = await commands.MemberConverter().convert(
            ctx=ctx, argument=argument
        )
        return cls(member, ctx.bot)

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

    def __hash__(self):
        return hash(self.person)
