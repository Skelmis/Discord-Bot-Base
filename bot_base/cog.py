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
    """A cog subclass with an async asnyc_hook method."""
    def __init__(self, bot: BotBase):
        self.bot: BotBase = bot

        internal_hook = getattr(self, "async_hook", None)
        if internal_hook:
            asyncio.create_task(internal_hook)

    if TYPE_CHECKING:
        async def async_hook(self) -> None:
            ...

