try:
    from nextcord import DiscordException
except ModuleNotFoundError:
    from disnake import DiscordException


class PrefixNotFound(DiscordException):
    """A prefix for this guild was not found."""


class ExistingEntry(DiscordException):
    """An entry was already found in the cache with this key."""


class NonExistentEntry(DiscordException):
    """No entry found in the cache with this key."""


class EventCancelled(DiscordException):
    """The waiting event was cancelled before a result was formed."""


class BlacklistedEntry(DiscordException):
    def __init__(self, message: str):
        self.message: str = message
