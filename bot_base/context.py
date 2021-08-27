import discord
from discord.ext import commands

from bot_base.wraps import Meta, WrappedChannel, WrappedPerson


class BotContext(commands.Context, Meta):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        self.message.channel = WrappedChannel(self.message.channel)  # noqa
        self.message.author = WrappedPerson(self.message.author)  # noqa
