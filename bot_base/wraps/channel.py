from typing import Union

from nextcord import abc
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedChannel(Meta, abc.GuildChannel, abc.PrivateChannel):  # noqa
    """Wraps nextcord.TextChannel for ease of stuff"""

    @classmethod
    async def convert(cls, ctx, argument: str) -> "WrappedChannel":
        channel: Union[
            abc.GuildChannel, abc.PrivateChannel
        ] = await commands.TextChannelConverter().convert(ctx=ctx, argument=argument)
        return cls(channel, ctx.bot)

    def __getattr__(self, item):
        return getattr(self._wrapped_item, item)
