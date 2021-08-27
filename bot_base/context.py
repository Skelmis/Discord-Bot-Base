from discord.ext import commands

from bot_base.wraps.meta import Meta


class BotContext(commands.Context, Meta):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
