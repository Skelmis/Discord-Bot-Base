from __future__ import annotations

from typing import TYPE_CHECKING

try:
    from nextcord.ext import commands
except ModuleNotFoundError:
    from disnake.ext import commands

from bot_base.wraps import Meta

if TYPE_CHECKING:
    from bot_base import BotBase


class BotContext(commands.Context, Meta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wrapped_bot: BotBase = self.bot

        self.message = self.bot.get_wrapped_message(self.message)
