from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

try:
    from nextcord.ext import commands
except ModuleNotFoundError:
    from disnake.ext import commands

if TYPE_CHECKING:
    from bot_base import BotBase


class Cog(commands.Cog):
    """A cog subclass which allows for async setup.

    Attempts to call an async method async_init
    on load, implement the method as required.
    """
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot

        internal_hook = getattr(self, "async_init", None)
        if internal_hook:
            try:
                asyncio.create_task(internal_hook)
            except RuntimeError as e:
                raise RuntimeError("Cog's must be loaded in an async context.") from e

    if TYPE_CHECKING:
        async def async_init(self) -> None:
            ...

