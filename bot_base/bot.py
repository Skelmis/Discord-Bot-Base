import motor as motor
from discord.ext import commands

from motor.motor_asyncio import AsyncIOMotorClient


class BotBase(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.mongo = AsyncIOMotorClient(kwargs.pop("mongo_url"))

        super().__init__(*args, **kwargs)
