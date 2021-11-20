from typing import Union

try:
    from nextcord import abc
    from nextcord.ext import commands
except ModuleNotFoundError:
    from discord import abc
    from discord.ext import commands

from bot_base.wraps.meta import Meta


class WrappedChannel(Meta, abc.GuildChannel, abc.PrivateChannel):  # noqa
    """Wraps nextcord.TextChannel for ease of stuff"""

    def __init__(self, channel: Union[abc.GuildChannel, abc.PrivateChannel]):
        self.channel: Union[abc.GuildChannel, abc.PrivateChannel] = channel

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from channel itself"""
        return getattr(self.channel, item)

    @property
    def __class__(self):
        return type(self.channel)

    def __eq__(self, other) -> bool:
        if not isinstance(other, (type(self.channel), WrappedChannel)):
            return False

        if isinstance(other, type(self.channel)):
            return other.id == self.channel.id

        return other.channel.id == self.channel.id


class WrappedChannelConvertor(commands.TextChannelConverter):
    """Return WrappedMember on :nextcord.Member"""

    async def convert(self, ctx, argument: str) -> WrappedChannel:
        channel: Union[abc.GuildChannel, abc.PrivateChannel] = await super().convert(
            ctx=ctx, argument=argument
        )
        return WrappedChannel(channel)
