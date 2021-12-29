try:
    from nextcord.ext import commands
except ModuleNotFoundError:
    from discord.ext import commands

from bot_base.wraps import Meta, WrappedChannel, WrappedMember, WrappedUser


class BotContext(commands.Context, Meta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.message.channel = WrappedChannel(self.message.channel, bot=self.bot)

        if not self.guild:
            self.message.author = WrappedUser(self.message.author, bot=self.bot)
        else:
            self.message.author = WrappedMember(self.message.author, bot=self.bot)
