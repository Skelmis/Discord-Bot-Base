from discord.ext import commands

from bot_base.db import MongoManager


class BotBase(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.db = MongoManager(kwargs.pop("mongo_url"))

        super().__init__(*args, **kwargs)
