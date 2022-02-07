try:
    import nextcord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import disnake as nextcord
    from disnake.ext import commands

from bot_base.wraps.meta import Meta


class WrappedMember(Meta, nextcord.Member):
    """Wraps discord.Member for ease of stuff"""

    @classmethod
    async def convert(cls, ctx, argument: str) -> "WrappedMember":
        member: nextcord.Member = await commands.MemberConverter().convert(
            ctx=ctx, argument=argument
        )
        return cls(member, ctx.bot)

    def __getattr__(self, item):
        return getattr(self._wrapped_item, item)
