from typing import Union

from discord import abc

from bot_base.wraps.meta import Meta


class WrappedChannel(Meta):
    """Wraps discord.TextChannel for ease of stuff"""

    def __init__(self, channel: Union[abc.GuildChannel, abc.PrivateChannel]):
        self.channel = channel

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from channel itself"""
        return getattr(self.channel, item)
