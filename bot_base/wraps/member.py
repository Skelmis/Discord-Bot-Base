from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from bot_base.vanity import Vanity

try:
    import nextcord
    from nextcord.ext import commands
except ModuleNotFoundError:
    import disnake as nextcord
    from disnake.ext import commands

from bot_base.wraps.meta import Meta

if TYPE_CHECKING:
    from bot_base import BotBase


class WrappedMember(Meta, nextcord.Member):
    """Wraps discord.Member for ease of stuff"""

    def __init__(self, wrapped_item, bot: BotBase):
        super().__init__(wrapped_item, bot)
        self._inviter: Optional[WrappedMember] = None

    @classmethod
    async def convert(cls, ctx, argument: str) -> WrappedMember:
        member: nextcord.Member = await commands.MemberConverter().convert(
            ctx=ctx, argument=argument
        )
        return cls(member, ctx.bot)

    def __getattr__(self, item):
        return getattr(self._wrapped_item, item)

    async def invited_by(self) -> Optional[Union[WrappedMember, Vanity]]:
        """Get the member who invited this user to the guild."""
        if self._inviter:
            return self._inviter

        for invite in self._wrapped_bot.invite_cache.values():
            if invite.used_by(self.id):
                if isinstance(invite.created_by, Vanity):
                    self._inviter = invite.created_by
                    return self._inviter

                self._inviter = await self._wrapped_bot.get_or_fetch_member(
                    invite.created_by, self.guild.id
                )

        return self._inviter
