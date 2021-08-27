from typing import Union

import discord

from bot_base.wraps.meta import Meta


class WrappedPerson(Meta):
    """Wraps discord.Member, discord.User for ease of stuff"""

    def __init__(self, channel: Union[discord.User, discord.Member]):
        self.channel = channel

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from author itself"""
        return getattr(self.channel, item)
