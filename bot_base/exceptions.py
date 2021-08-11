from discord import DiscordException


class PrefixNotFound(DiscordException):
    """A prefix for this guild was not found."""
