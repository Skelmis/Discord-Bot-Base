from typing import Union

from nextcord import abc
from nextcord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedChannel(Meta):
    """Wraps nextcord.TextChannel for ease of stuff"""

    def __init__(self, channel: Union[abc.GuildChannel, abc.PrivateChannel]):
        self.channel = channel

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from channel itself"""
        return getattr(self.channel, item)

    @property
    def __class__(self):
        return type(self.channel)

    def __eq__(self, other):
        if not isinstance(other, (type(self.channel), WrappedChannel)):
            return False

        if isinstance(other, type(self.channel)):
            return other.id == self.channel.id

        return other.channel.id == self.channel.id


class WrappedChannelConvertor(commands.TextChannelConverter):
    """Return WrappedPerson on :nextcord.Member"""

    async def convert(self, ctx, argument: str) -> WrappedChannel:
        channel: Union[abc.GuildChannel, abc.PrivateChannel] = await super().convert(
            ctx=ctx, argument=argument
        )
        return WrappedChannel(channel)
