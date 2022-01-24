import nextcord as discord
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedMember(Meta, discord.Member):
    """Wraps discord.Member for ease of stuff"""

    @classmethod
    async def convert(cls, ctx, argument: str) -> "WrappedMember":
        member: discord.Member = await commands.MemberConverter().convert(
            ctx=ctx, argument=argument
        )
        return cls(member, ctx.bot)
