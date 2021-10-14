from typing import Union

import nextcord

from bot_base.wraps.meta import Meta


class WrappedPerson(Meta):
    """Wraps nextcord.Member, nextcord.User for ease of stuff"""

    def __init__(self, channel: Union[nextcord.User, nextcord.Member]):
        self.person = channel

    def __getattr__(self, item):
        """Anything not found within Meta should be returned from author itself"""
        return getattr(self.person, item)

    @property
    def __class__(self):
        return type(self.person)

    def __eq__(self, other):
        if not isinstance(other, (type(self.person), WrappedPerson)):
            return False

        if isinstance(other, type(self.person)):
            return other.id == self.person.id

        return other.person.id == self.person.id
